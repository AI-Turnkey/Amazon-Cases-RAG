from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import json
import os
import sys
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from functools import wraps

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_optimized_chat_history(user_id, limit=10):
    """Get optimized chat history with pagination and message limiting"""
    try:
        if not supabase:
            return []
            
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
        if not supabase:
            return
            
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
    }), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"🔐 Login attempt for: {email}")
        
        if not supabase:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                session['user'] = {
                    'id': response.user.id,
                    'email': response.user.email
                }
                session['access_token'] = response.session.access_token
                print(f"✅ Login successful for: {email}")
                return redirect(url_for('index'))
            else:
                print(f"❌ Login failed - no user returned")
                flash('Invalid credentials', 'error')
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    full_name = request.form['full_name']
    
    print(f"📝 Signup attempt for: {email}")
    
    if not supabase:
        flash('Database connection error', 'error')
        return render_template('login.html')
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if response.user:
            flash('Account created successfully! You can now sign in.', 'success')
            print(f"✅ Signup successful for: {email}")
        else:
            flash('Error creating account', 'error')
            print(f"❌ Signup failed - no user returned")
            
    except Exception as e:
        print(f"❌ Signup error: {str(e)}")
        flash(f'Signup error: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    try:
        if supabase:
            supabase.auth.sign_out()
    except Exception as e:
        print(f"Logout error: {e}")
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if not supabase:
        flash('Database connection error', 'error')
        return redirect(url_for('logout'))
    
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
        return redirect(url_for('logout'))

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

@app.route('/new_chat', methods=['POST'])
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

@app.route('/load_chat/<chat_id>')
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

@app.route('/get_chat_histories')
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

@app.route('/delete_chat/<chat_id>', methods=['DELETE'])
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 Starting Flask application on port {port}...")
    print(f"🔧 Debug mode: {DEBUG}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🗄️ Supabase Connected: {'✅ Yes' if supabase else '❌ No'}")
    app.run(debug=DEBUG, host='0.0.0.0', port=port)
