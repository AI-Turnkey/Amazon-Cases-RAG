from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import json
import os
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from functools import wraps
from config import *

app = Flask(__name__, 
           template_folder='../templates', 
           static_folder='../static')
app.secret_key = SECRET_KEY

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Supabase client: {e}")
    supabase = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_optimized_chat_history(user_id, limit=10):
    """Get optimized chat history with pagination and message limiting"""
    try:
        # Get recent chats
        chats_response = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(limit).execute()
        chats = chats_response.data
        
        # For each chat, get only the latest 20 messages to avoid memory overload
        for chat in chats:
            messages_response = supabase.table('messages').select('*').eq('chat_id', chat['id']).order('created_at', desc=True).limit(20).execute()
            # Reverse to get chronological order
            chat['messages'] = list(reversed(messages_response.data))
            
        return chats
    except Exception as e:
        print(f"❌ Error getting optimized chat history: {e}")
        return []

def cleanup_old_chats(user_id, keep_count=MAX_CHAT_HISTORIES):
    """Clean up old chats to prevent database bloat"""
    try:
        # Get all user chats ordered by update time
        all_chats = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
        
        if len(all_chats.data) > keep_count:
            # Delete oldest chats beyond the limit
            chats_to_delete = all_chats.data[keep_count:]
            
            for chat in chats_to_delete:
                # Delete messages first
                supabase.table('messages').delete().eq('chat_id', chat['id']).execute()
                # Delete chat
                supabase.table('chats').delete().eq('id', chat['id']).execute()
                
            print(f"🧹 Cleaned up {len(chats_to_delete)} old chats")
            
    except Exception as e:
        print(f"❌ Error cleaning up old chats: {e}")

# Health check endpoint for Railway
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'supabase_connected': supabase is not None
    })

@app.route('/')
@login_required
def index():
    if not supabase:
        flash('Database connection error', 'error')
        return redirect(url_for('auth.logout'))
    
    user_id = session['user']['id']
    
    try:
        # Clean up old chats periodically
        cleanup_old_chats(user_id)
        
        # Get optimized chat history
        chats = get_optimized_chat_history(user_id, MAX_CHAT_HISTORIES)
        
        print(f"📊 Found {len(chats)} chats for user {user_id}")
        
        # Get current chat (most recent or create new one)
        if chats:
            current_chat = chats[0]
            print(f"💬 Current chat has {len(current_chat['messages'])} messages")
        else:
            # Create a new chat
            new_chat_response = supabase.table('chats').insert({
                'user_id': user_id,
                'title': f"Chat {datetime.now().strftime('%H:%M')}"
            }).execute()
            current_chat = new_chat_response.data[0]
            current_chat['messages'] = []
            chats = [current_chat]
            print(f"🆕 Created new chat: {current_chat['id']}")
        
        session['current_chat_id'] = current_chat['id']
        
        return render_template('index.html', 
                             chat_histories=chats, 
                             current_chat=current_chat,
                             user=session['user'])
                             
    except Exception as e:
        print(f"❌ Database error in index: {e}")
        flash('Error loading chats', 'error')
        return redirect(url_for('auth.logout'))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        user_message = request.form['message']
        image_data = request.files.get('image')
        user_id = session['user']['id']
        current_chat_id = session.get('current_chat_id')
        
        if not current_chat_id:
            return jsonify({'error': 'No active chat found'}), 400
        
        # Get current chat
        chat_response = supabase.table('chats').select('*').eq('id', current_chat_id).eq('user_id', user_id).execute()
        
        if not chat_response.data:
            return jsonify({'error': 'Chat not found'}), 404
        
        current_chat = chat_response.data[0]
        
        # Store user message
        user_message_data = {
            'chat_id': current_chat['id'],
            'role': 'user',
            'content': user_message,
            'has_image': image_data is not None
        }
        
        stored_image_info = None
        final_query = user_message
        
        # Handle image upload if present
        if image_data and image_data.filename:
            try:
                filename = f"chat_image_{uuid.uuid4()}_{image_data.filename}"
                
                # Upload to Supabase storage
                upload_response = supabase.storage.from_("chat-images").upload(
                    filename, 
                    image_data.read(),
                    file_options={"content-type": image_data.content_type}
                )
                
                if upload_response:
                    # Get public URL
                    image_url = supabase.storage.from_("chat-images").get_public_url(filename)
                    user_message_data['image_url'] = image_url
                    
                    stored_image_info = {
                        'filename': filename,
                        'url': image_url,
                        'content_type': image_data.content_type
                    }
                    
                    # Enhanced query for N8N webhook
                    final_query = f"""
Image Analysis Request:
User Message: {user_message}
Image URL: {image_url}

Please analyze the attached image and respond to the user's message in context.
"""
                    
                    print(f"📸 Image uploaded successfully: {filename}")
                
            except Exception as upload_error:
                print(f"❌ Image upload error: {upload_error}")
                return jsonify({'error': f'Image upload failed: {str(upload_error)}'}), 500
        
        # Insert user message
        supabase.table('messages').insert(user_message_data).execute()
        
        # Get recent conversation context (limit to last 10 messages for efficiency)
        recent_messages = supabase.table('messages').select('*').eq('chat_id', current_chat['id']).order('created_at', desc=True).limit(10).execute()
        
        # Build conversation context
        conversation_context = []
        for msg in reversed(recent_messages.data[:-1]):  # Exclude the current message
            role = "User" if msg['role'] == 'user' else "Assistant"
            conversation_context.append(f"{role}: {msg['content']}")
        
        context_text = "\n".join(conversation_context) if conversation_context else "This is the start of the conversation."
        
        # Prepare webhook payload
        main_payload = {
            "user_message": final_query,
            "conversation_context": context_text,
            "chat_id": current_chat['id'],
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to N8N webhook
        try:
            main_response = requests.post(
                N8N_WEBHOOK_URL,
                json=main_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            print(f"📨 N8N Response Status: {main_response.status_code}")
            
            if main_response.status_code == 200:
                try:
                    response_text = main_response.text.strip()
                    
                    try:
                        response_data = main_response.json()
                        if isinstance(response_data, str):
                            bot_message = response_data
                        elif isinstance(response_data, dict):
                            bot_message = (
                                response_data.get('output') or
                                response_data.get('response') or
                                response_data.get('message') or 
                                response_data.get('text') or
                                str(response_data)
                            )
                        else:
                            bot_message = str(response_data)
                    except json.JSONDecodeError:
                        bot_message = response_text
                        
                except Exception as parse_error:
                    print(f"❌ Error processing response: {parse_error}")
                    bot_message = f'Error processing AI response: {str(parse_error)}'
                    
            else:
                bot_message = f'AI service returned status {main_response.status_code}.'
        
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            bot_message = f'Error connecting to AI service: {str(e)}'
        
        # Store bot response
        supabase.table('messages').insert({
            'chat_id': current_chat['id'],
            'role': 'assistant',
            'content': bot_message,
            'has_image': False
        }).execute()
        
        # Update chat timestamp
        supabase.table('chats').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', current_chat['id']).execute()
        
        return jsonify({
            'user_message': user_message,
            'bot_response': bot_message,
            'chat_id': current_chat['id'],
            'has_image': stored_image_info is not None,
            'image_info': stored_image_info
        })
    
    except Exception as e:
        print(f"❌ Error in send_message: {e}")
        return jsonify({'error': str(e)}), 500

# Import auth routes
from app.auth import auth_bp
app.register_blueprint(auth_bp)

# Import chat routes
from app.chat import chat_bp
app.register_blueprint(chat_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", PORT))
    app.run(debug=DEBUG, host='0.0.0.0', port=port)
