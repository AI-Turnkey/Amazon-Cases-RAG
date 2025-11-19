from flask import Blueprint, jsonify, session, request
from datetime import datetime
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, MAX_CHAT_HISTORIES
from functools import wraps

chat_bp = Blueprint('chat', __name__)

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Error initializing Supabase in chat: {e}")
    supabase = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@chat_bp.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        user_id = session['user']['id']
        
        new_chat_response = supabase.table('chats').insert({
            'user_id': user_id,
            'title': f"Chat {datetime.now().strftime('%H:%M')}"
        }).execute()
        
        new_chat = new_chat_response.data[0]
        session['current_chat_id'] = new_chat['id']
        
        return jsonify({
            'chat_id': new_chat['id'],
            'title': new_chat['title']
        })
        
    except Exception as e:
        print(f"❌ Error creating new chat: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/load_chat/<chat_id>')
@login_required
def load_chat(chat_id):
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        user_id = session['user']['id']
        
        chat_response = supabase.table('chats').select('*').eq('id', chat_id).eq('user_id', user_id).execute()
        
        if not chat_response.data:
            return jsonify({'error': 'Chat not found'}), 404
        
        chat = chat_response.data[0]
        
        # Get messages for this chat (limit to recent 30 for performance)
        messages_response = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at').limit(30).execute()
        
        chat['messages'] = messages_response.data
        session['current_chat_id'] = chat_id
        
        print(f"📖 Loaded chat {chat_id} with {len(chat['messages'])} messages")
        
        return jsonify(chat)
        
    except Exception as e:
        print(f"❌ Error loading chat: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/get_chat_histories')
@login_required
def get_chat_histories():
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        user_id = session['user']['id']
        
        chats_response = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(MAX_CHAT_HISTORIES).execute()
        
        return jsonify(chats_response.data)
        
    except Exception as e:
        print(f"❌ Error getting chat histories: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/delete_chat/<chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        user_id = session['user']['id']
        
        # Verify chat belongs to user
        chat_response = supabase.table('chats').select('*').eq('id', chat_id).eq('user_id', user_id).execute()
        
        if not chat_response.data:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Get messages with images to clean up storage
        messages_with_images = supabase.table('messages').select('*').eq('chat_id', chat_id).eq('has_image', True).execute()
        
        # Delete images from storage
        for message in messages_with_images.data:
            if message.get('image_url'):
                try:
                    # Extract filename from URL and delete from storage
                    filename = message['image_url'].split('/')[-1]
                    supabase.storage.from_("chat-images").remove([filename])
                    print(f"🗑️ Deleted image from storage: {filename}")
                except Exception as storage_error:
                    print(f"⚠️ Could not delete image from storage: {storage_error}")
        
        # Delete all messages in the chat
        supabase.table('messages').delete().eq('chat_id', chat_id).execute()
        
        # Delete the chat
        supabase.table('chats').delete().eq('id', chat_id).execute()
        
        print(f"🗑️ Deleted chat {chat_id} for user {user_id}")
        
        return jsonify({'success': True, 'message': 'Chat deleted successfully'})
        
    except Exception as e:
        print(f"❌ Error deleting chat: {e}")
        return jsonify({'error': str(e)}), 500
