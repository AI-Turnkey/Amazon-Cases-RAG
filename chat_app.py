# import flask
# from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
# import requests
# import json
# import os
# from datetime import datetime
# import uuid
# from supabase import create_client, Client
# from functools import wraps

# # Try to import configuration from config.py
# try:
#     from config import N8N_WEBHOOK_URL, SECRET_KEY, DEBUG, PORT, MAX_CHAT_HISTORIES, SUPABASE_URL, SUPABASE_KEY
# except ImportError:
#     print("Warning: config.py not found. Using default configuration.")
#     print("Please copy config_example.py to config.py and update the settings.")
#     N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/your-webhook-path"
#     SECRET_KEY = 'your-secret-key-change-this'
#     DEBUG = True
#     PORT = 5000
#     MAX_CHAT_HISTORIES = 3
#     SUPABASE_URL = "https://your-project.supabase.co"
#     SUPABASE_KEY = "your-anon-key"

# app = Flask(__name__)
# app.secret_key = SECRET_KEY

# # Initialize Supabase client
# try:
#     supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
#     print("✅ Supabase client initialized successfully")
# except Exception as e:
#     print(f"❌ Error initializing Supabase client: {e}")
#     supabase = None

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user' not in session:
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# # Debug routes
# @app.route('/test_supabase')
# def test_supabase():
#     try:
#         if not supabase:
#             return "❌ Supabase client not initialized"
        
#         result = supabase.table('user_profiles').select('*').limit(1).execute()
#         return f"""
#         <h3>✅ Supabase Connection Test</h3>
#         <p><strong>URL:</strong> {SUPABASE_URL}</p>
#         <p><strong>Key starts with:</strong> {SUPABASE_KEY[:20]}...</p>
#         <p><strong>Connection:</strong> Successful!</p>
#         <p><strong>Result:</strong> {len(result.data)} records found</p>
#         """
#     except Exception as e:
#         return f"""
#         <h3>❌ Supabase Connection Failed</h3>
#         <p><strong>URL:</strong> {SUPABASE_URL}</p>
#         <p><strong>Key starts with:</strong> {SUPABASE_KEY[:20]}...</p>
#         <p><strong>Error:</strong> {str(e)}</p>
#         """

# @app.route('/debug_config')
# def debug_config():
#     return f"""
#     <h3>🔧 Configuration Debug</h3>
#     <p><strong>SUPABASE_URL:</strong> {SUPABASE_URL}</p>
#     <p><strong>SUPABASE_KEY starts with:</strong> {SUPABASE_KEY[:30]}...</p>
#     <p><strong>SECRET_KEY starts with:</strong> {SECRET_KEY[:10]}...</p>
#     <p><strong>DEBUG:</strong> {DEBUG}</p>
#     <p><strong>PORT:</strong> {PORT}</p>
#     <p><strong>N8N_WEBHOOK_URL:</strong> {N8N_WEBHOOK_URL}</p>
#     """

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
        
#         print(f"🔐 Login attempt for: {email}")
        
#         if not supabase:
#             flash('Database connection error', 'error')
#             return render_template('login.html')
        
#         try:
#             response = supabase.auth.sign_in_with_password({
#                 "email": email,
#                 "password": password
#             })
            
#             if response.user:
#                 session['user'] = {
#                     'id': response.user.id,
#                     'email': response.user.email
#                 }
#                 session['access_token'] = response.session.access_token
#                 print(f"✅ Login successful for: {email}")
#                 return redirect(url_for('index'))
#             else:
#                 print(f"❌ Login failed - no user returned")
#                 flash('Invalid credentials', 'error')
                
#         except Exception as e:
#             print(f"❌ Login error: {str(e)}")
#             flash(f'Login error: {str(e)}', 'error')
    
#     return render_template('login.html')

# @app.route('/signup', methods=['POST'])
# def signup():
#     email = request.form['email']
#     password = request.form['password']
#     full_name = request.form['full_name']
    
#     print(f"📝 Signup attempt for: {email}")
    
#     if not supabase:
#         flash('Database connection error', 'error')
#         return render_template('login.html')
    
#     try:
#         response = supabase.auth.sign_up({
#             "email": email,
#             "password": password,
#             "options": {
#                 "data": {
#                     "full_name": full_name
#                 }
#             }
#         })
        
#         if response.user:
#             flash('Account created successfully! You can now sign in.', 'success')
#             print(f"✅ Signup successful for: {email}")
#         else:
#             flash('Error creating account', 'error')
#             print(f"❌ Signup failed - no user returned")
            
#     except Exception as e:
#         print(f"❌ Signup error: {str(e)}")
#         flash(f'Signup error: {str(e)}', 'error')
    
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     try:
#         if supabase:
#             supabase.auth.sign_out()
#     except Exception as e:
#         print(f"Logout error: {e}")
#     session.clear()
#     return redirect(url_for('login'))

# @app.route('/')
# @login_required
# def index():
#     if not supabase:
#         flash('Database connection error', 'error')
#         return redirect(url_for('logout'))
    
#     user_id = session['user']['id']
    
#     try:
#         # Get user's chats from database
#         chats_response = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(MAX_CHAT_HISTORIES).execute()
#         chats = chats_response.data
        
#         print(f"📊 Found {len(chats)} chats for user {user_id}")
        
#         # Get current chat (most recent or create new one)
#         if chats:
#             current_chat = chats[0]
#             # Get messages for current chat
#             messages_response = supabase.table('messages').select('*').eq('chat_id', current_chat['id']).order('created_at').execute()
#             current_chat['messages'] = messages_response.data
#             print(f"💬 Current chat has {len(current_chat['messages'])} messages")
#         else:
#             # Create a new chat
#             new_chat_response = supabase.table('chats').insert({
#                 'user_id': user_id,
#                 'title': f"Chat {datetime.now().strftime('%H:%M')}"
#             }).execute()
#             current_chat = new_chat_response.data[0]
#             current_chat['messages'] = []
#             chats = [current_chat]
#             print(f"🆕 Created new chat: {current_chat['id']}")
        
#         session['current_chat_id'] = current_chat['id']
        
#         return render_template('index.html', 
#                              chat_histories=chats, 
#                              current_chat=current_chat,
#                              user=session['user'])
                             
#     except Exception as e:
#         print(f"❌ Database error in index: {e}")
#         flash('Error loading chats', 'error')
#         return redirect(url_for('logout'))

# @app.route('/send_message', methods=['POST'])
# @login_required
# def send_message():
#     if not supabase:
#         return jsonify({'error': 'Database connection error'}), 500
    
#     try:
#         data = request.get_json()
#         user_message = data.get('message', '').strip()
        
#         if not user_message:
#             return jsonify({'error': 'Message cannot be empty'}), 400
        
#         user_id = session['user']['id']
#         current_chat_id = session.get('current_chat_id')
        
#         # Get or create current chat
#         if current_chat_id:
#             try:
#                 chat_response = supabase.table('chats').select('*').eq('id', current_chat_id).eq('user_id', user_id).execute()
#                 if chat_response.data:
#                     current_chat = chat_response.data[0]
#                 else:
#                     raise Exception("Chat not found")
#             except:
#                 # Create new chat if current one doesn't exist
#                 new_chat_response = supabase.table('chats').insert({
#                     'user_id': user_id,
#                     'title': user_message[:30] + "..." if len(user_message) > 30 else user_message
#                 }).execute()
#                 current_chat = new_chat_response.data[0]
#                 session['current_chat_id'] = current_chat['id']
        
#         # Add user message to database first
#         user_msg_response = supabase.table('messages').insert({
#             'chat_id': current_chat['id'],
#             'role': 'user',
#             'content': user_message
#         }).execute()
        
#         # Get the last 10 messages for context (including the one we just added)
#         context_messages = supabase.table('messages').select('role, content, created_at').eq('chat_id', current_chat['id']).order('created_at').limit(10).execute()
        
#         # Format conversation history for N8N
#         conversation_history = []
#         for msg in context_messages.data:
#             conversation_history.append({
#                 'role': msg['role'],
#                 'content': msg['content'],
#                 'timestamp': msg['created_at']
#             })
        
#         print(f"📝 Sending {len(conversation_history)} messages as context to N8N")
        
#         # Update chat title if it's the first message
#         messages_count = supabase.table('messages').select('id', count='exact').eq('chat_id', current_chat['id']).execute()
#         if messages_count.count == 1:  # First message
#             supabase.table('chats').update({
#                 'title': user_message[:30] + "..." if len(user_message) > 30 else user_message,
#                 'updated_at': datetime.now().isoformat()
#             }).eq('id', current_chat['id']).execute()
        
#         # Send message to N8N webhook with conversation context
#         bot_message = "Sorry, I could not get a response from the AI service."
        
#         try:
#             webhook_payload = {
#                 'message': user_message,
#                 'conversation_history': conversation_history,
#                 'chat_id': current_chat['id'],
#                 'user_id': user_id,
#                 'timestamp': datetime.now().isoformat(),
#                 'context_message_count': len(conversation_history)
#             }
            
#             print(f"🔗 Sending to N8N: {webhook_payload}")
            
#             response = requests.post(
#                 N8N_WEBHOOK_URL, 
#                 json=webhook_payload,
#                 headers={'Content-Type': 'application/json'},
#                 timeout=60  # Increased timeout to 60 seconds
#             )
            
#             print(f"📨 N8N Response Status: {response.status_code}")
#             print(f"📨 N8N Response Headers: {dict(response.headers)}")
#             print(f"📨 N8N Response Text: {response.text[:500]}...")  # First 500 chars
            
#             if response.status_code == 200:
#                 try:
#                     # Handle the response text directly first
#                     response_text = response.text.strip()
#                     print(f"🔍 Raw response text: {response_text[:200]}...")
                    
#                     # Try to parse as JSON
#                     try:
#                         n8n_response = response.json()
#                         print(f"📊 Parsed JSON response: {type(n8n_response)}")
#                     except json.JSONDecodeError as json_err:
#                         print(f"❌ JSON decode error: {json_err}")
#                         # If JSON parsing fails, use the raw text
#                         bot_message = response_text
#                         print(f"✅ Using raw text as response")
#                     else:
#                         # Successfully parsed JSON, now extract the message
#                         bot_message = None
                        
#                         print(f"🔍 Response type: {type(n8n_response)}")
                        
#                         if isinstance(n8n_response, str):
#                             bot_message = n8n_response
#                             print("✅ String response")
#                         elif isinstance(n8n_response, list) and len(n8n_response) > 0:
#                             print(f"✅ Array response with {len(n8n_response)} items")
#                             first_item = n8n_response[0]
#                             print(f"🔍 First item type: {type(first_item)}")
                            
#                             if isinstance(first_item, dict):
#                                 print(f"🔍 First item keys: {list(first_item.keys())}")
#                                 bot_message = (
#                                     first_item.get('output') or      # This should match your N8N response
#                                     first_item.get('response') or
#                                     first_item.get('message') or 
#                                     first_item.get('text') or
#                                     first_item.get('result') or
#                                     str(first_item)
#                                 )
#                                 if first_item.get('output'):
#                                     print("✅ Found 'output' field")
#                             else:
#                                 bot_message = str(first_item)
#                         elif isinstance(n8n_response, dict):
#                             print(f"✅ Object response with keys: {list(n8n_response.keys())}")
#                             bot_message = (
#                                 n8n_response.get('output') or
#                                 n8n_response.get('response') or
#                                 n8n_response.get('message') or 
#                                 n8n_response.get('text') or
#                                 n8n_response.get('result') or
#                                 str(n8n_response)
#                             )
                        
#                         if not bot_message:
#                             print("❌ Could not extract message from response")
#                             bot_message = f'Received response but could not parse it: {str(n8n_response)[:200]}...'
#                         else:
#                             print(f"✅ Extracted message: {bot_message[:100]}...")
                            
#                 except Exception as parse_error:
#                     print(f"❌ Error processing N8N response: {parse_error}")
#                     bot_message = f'Error processing AI response: {str(parse_error)}'
                    
#             elif response.status_code == 202:
#                 print("📨 Received 202 Accepted - N8N might be processing asynchronously")
#                 bot_message = 'Your request is being processed. Please try asking again in a moment.'
#             else:
#                 print(f"❌ N8N returned status {response.status_code}")
#                 bot_message = f'AI service returned status {response.status_code}. Response: {response.text[:200]}...'
        
#         except requests.exceptions.Timeout:
#             print("⏰ Request to N8N timed out")
#             bot_message = 'The AI service is taking too long to respond. Please try again.'
#         except requests.exceptions.ConnectionError:
#             print("🔌 Connection error to N8N")
#             bot_message = 'Could not connect to the AI service. Please check your internet connection and try again.'
#         except requests.exceptions.RequestException as e:
#             print(f"❌ N8N Request error: {e}")
#             bot_message = f'Network error connecting to AI service: {str(e)}'
#         except Exception as e:
#             print(f"❌ Unexpected error: {e}")
#             bot_message = f'Unexpected error: {str(e)}'
        
#         # Add bot response to database
#         bot_msg_response = supabase.table('messages').insert({
#             'chat_id': current_chat['id'],
#             'role': 'assistant',
#             'content': bot_message
#         }).execute()
        
#         # Update chat's updated_at timestamp
#         supabase.table('chats').update({
#             'updated_at': datetime.now().isoformat()
#         }).eq('id', current_chat['id']).execute()
        
#         return jsonify({
#             'user_message': user_message,
#             'bot_response': bot_message,
#             'chat_id': current_chat['id']
#         })
    
#     except Exception as e:
#         print(f"❌ Error in send_message: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/new_chat', methods=['POST'])
# @login_required
# def new_chat():
#     if not supabase:
#         return jsonify({'error': 'Database connection error'}), 500
    
#     try:
#         user_id = session['user']['id']
        
#         # Create new chat
#         new_chat_response = supabase.table('chats').insert({
#             'user_id': user_id,
#             'title': f"Chat {datetime.now().strftime('%H:%M')}"
#         }).execute()
        
#         new_chat = new_chat_response.data[0]
#         session['current_chat_id'] = new_chat['id']
        
#         return jsonify({
#             'chat_id': new_chat['id'],
#             'title': new_chat['title']
#         })
        
#     except Exception as e:
#         print(f"❌ Error creating new chat: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/load_chat/<chat_id>')
# @login_required
# def load_chat(chat_id):
#     if not supabase:
#         return jsonify({'error': 'Database connection error'}), 500
    
#     try:
#         user_id = session['user']['id']
        
#         # Verify chat belongs to user and get chat info
#         chat_response = supabase.table('chats').select('*').eq('id', chat_id).eq('user_id', user_id).execute()
        
#         if not chat_response.data:
#             return jsonify({'error': 'Chat not found'}), 404
        
#         chat = chat_response.data[0]
        
#         # Get messages for this chat
#         messages_response = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at').execute()
        
#         chat['messages'] = messages_response.data
#         session['current_chat_id'] = chat_id
        
#         print(f"📖 Loaded chat {chat_id} with {len(chat['messages'])} messages")
        
#         return jsonify(chat)
        
#     except Exception as e:
#         print(f"❌ Error loading chat: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/get_chat_histories')
# @login_required
# def get_chat_histories_api():
#     if not supabase:
#         return jsonify({'error': 'Database connection error'}), 500
    
#     try:
#         user_id = session['user']['id']
        
#         # Get user's chats
#         chats_response = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(MAX_CHAT_HISTORIES).execute()
        
#         return jsonify(chats_response.data)
        
#     except Exception as e:
#         print(f"❌ Error getting chat histories: {e}")
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     print(f"🚀 Starting Flask application...")
#     print(f"🔧 Debug mode: {DEBUG}")
#     print(f"🌐 Port: {PORT}")
#     print(f"🔗 N8N Webhook URL: {N8N_WEBHOOK_URL}")
#     print(f"🗄️ Supabase URL: {SUPABASE_URL}")
#     print(f"📱 Open your browser and go to: http://localhost:{PORT}")
#     print(f"🔍 Debug URLs:")
#     print(f"   - http://localhost:{PORT}/debug_config")
#     print(f"   - http://localhost:{PORT}/test_supabase")
#     app.run(debug=DEBUG, port=PORT, host='127.0.0.1')






























































import flask
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import json
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from supabase import create_client, Client
from functools import wraps

# Import configuration from config.py
try:
    from config import N8N_WEBHOOK_URL, N8N_IMAGE_WEBHOOK_URL, SECRET_KEY, DEBUG, PORT, MAX_CHAT_HISTORIES, SUPABASE_URL, SUPABASE_KEY
except ImportError:
    print("❌ config.py not found. Please create config.py with your settings.")
    exit(1)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize Supabase client
supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
        
        # Test the connection
        test_response = supabase.table('chats').select('*').limit(1).execute()
        print("✅ Supabase connection test successful")
    else:
        print("❌ Invalid Supabase credentials in config")
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

# Debug routes
@app.route('/test_supabase')
def test_supabase():
    try:
        if not supabase:
            return f"""
            <h3>❌ Supabase Client Not Initialized</h3>
            <p><strong>URL:</strong> {SUPABASE_URL}</p>
            <p><strong>Error:</strong> Client not initialized</p>
            """
        
        result = supabase.table('chats').select('*').limit(1).execute()
        return f"""
        <h3>✅ Supabase Connection Test</h3>
        <p><strong>URL:</strong> {SUPABASE_URL}</p>
        <p><strong>Connection:</strong> Successful!</p>
        <p><strong>Tables accessible:</strong> Yes ({len(result.data)} records found)</p>
        """
    except Exception as e:
        return f"""
        <h3>❌ Supabase Connection Failed</h3>
        <p><strong>URL:</strong> {SUPABASE_URL}</p>
        <p><strong>Error:</strong> {str(e)}</p>
        """

@app.route('/debug_config')
def debug_config():
    return f"""
    <h3>🔧 Configuration Debug</h3>
    <p><strong>SUPABASE_URL:</strong> {SUPABASE_URL}</p>
    <p><strong>SUPABASE_KEY starts with:</strong> {SUPABASE_KEY[:30] if SUPABASE_KEY else 'None'}...</p>
    <p><strong>SECRET_KEY starts with:</strong> {SECRET_KEY[:10]}...</p>
    <p><strong>DEBUG:</strong> {DEBUG}</p>
    <p><strong>PORT:</strong> {PORT}</p>
    <p><strong>N8N_WEBHOOK_URL:</strong> {N8N_WEBHOOK_URL}</p>
    <p><strong>N8N_IMAGE_WEBHOOK_URL:</strong> {N8N_IMAGE_WEBHOOK_URL}</p>
    <p><strong>Supabase Client:</strong> {'✅ Initialized' if supabase else '❌ Not Initialized'}</p>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"🔐 Login attempt for: {email}")
        
        if not supabase:
            flash('Database connection error. Please check configuration.', 'error')
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
        flash('Database connection error. Please check configuration.', 'error')
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
        flash('Database connection error. Please check configuration.', 'error')
        return redirect(url_for('logout'))
    
    user_id = session['user']['id']
    
    try:
        # Get user's chats from database
        chats_response = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).limit(MAX_CHAT_HISTORIES).execute()
        chats = chats_response.data
        
        print(f"📊 Found {len(chats)} chats for user {user_id}")
        
        # Get current chat (most recent or create new one)
        if chats:
            current_chat = chats[0]
            # Get messages for current chat
            messages_response = supabase.table('messages').select('*').eq('chat_id', current_chat['id']).order('created_at').execute()
            current_chat['messages'] = messages_response.data
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
        flash('Error loading chats. Please try again.', 'error')
        return redirect(url_for('logout'))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if not supabase:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        # Handle both JSON and form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            user_message = request.form.get('message', '').strip()
            image_file = request.files.get('image')
            
            image_data = None
            stored_image_info = None
            
            if image_file and image_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    return jsonify({'error': 'Unsupported image format. Please upload PNG, JPG, JPEG, GIF, WEBP, BMP, or TIFF files.'}), 400
                
                # Check file size (max 10MB)
                image_file.seek(0, 2)
                file_size = image_file.tell()
                image_file.seek(0)
                
                if file_size > 10 * 1024 * 1024:
                    return jsonify({'error': 'Image file too large. Please upload an image smaller than 10MB.'}), 400
                
                # Read image content
                image_content = image_file.read()
                
                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"
                
                try:
                    # Upload to Supabase Storage
                    storage_response = supabase.storage.from_("chat-images").upload(
                        path=unique_filename,
                        file=image_content,
                        file_options={"content-type": f"image/{file_extension}"}
                    )
                    
                    # Get public URL
                    public_url = supabase.storage.from_("chat-images").get_public_url(unique_filename)
                    
                    stored_image_info = {
                        'url': public_url,
                        'filename': secure_filename(image_file.filename),
                        'size': file_size,
                        'storage_path': unique_filename
                    }
                    
                    # For sending to N8N webhook (binary)
                    image_data = {
                        'binary': image_content,
                        'mime_type': f"image/{file_extension}",
                        'filename': secure_filename(image_file.filename),
                        'size': file_size
                    }
                    
                    print(f"📸 Image uploaded to Supabase Storage: {unique_filename}")
                    
                except Exception as storage_error:
                    print(f"❌ Storage upload failed: {storage_error}")
                    return jsonify({'error': 'Failed to upload image. Please try again.'}), 500
        else:
            # Handle regular JSON data
            data = request.get_json()
            user_message = data.get('message', '').strip()
            image_data = None
            stored_image_info = None
        
        if not user_message and not image_data:
            return jsonify({'error': 'Message or image is required'}), 400
        
        user_id = session['user']['id']
        current_chat_id = session.get('current_chat_id')
        
        # Get or create current chat
        if current_chat_id:
            try:
                chat_response = supabase.table('chats').select('*').eq('id', current_chat_id).eq('user_id', user_id).execute()
                if chat_response.data:
                    current_chat = chat_response.data[0]
                else:
                    raise Exception("Chat not found")
            except:
                # Create new chat if current one doesn't exist
                chat_title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                if not chat_title and image_data:
                    chat_title = f"Image: {image_data['filename']}"
                
                new_chat_response = supabase.table('chats').insert({
                    'user_id': user_id,
                    'title': chat_title
                }).execute()
                current_chat = new_chat_response.data[0]
                session['current_chat_id'] = current_chat['id']
        
        # Add user message to database with image info
        user_message_data = {
            'chat_id': current_chat['id'],
            'role': 'user',
            'content': user_message if user_message else ""
        }
        
        # Add image data if present
        if stored_image_info:
            user_message_data['has_image'] = True
            user_message_data['image_url'] = stored_image_info['url']
            user_message_data['image_filename'] = stored_image_info['filename']
            user_message_data['image_size'] = stored_image_info['size']
        else:
            user_message_data['has_image'] = False
        
        user_msg_response = supabase.table('messages').insert(user_message_data).execute()
        
        # Get the last 10 messages for context
        context_messages = supabase.table('messages').select('role, content, created_at').eq('chat_id', current_chat['id']).order('created_at').limit(10).execute()
        
        # Format conversation history for N8N
        conversation_history = []
        for msg in context_messages.data:
            conversation_history.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['created_at']
            })
        
        print(f"📝 Sending {len(conversation_history)} messages as context")
        
        # Update chat title if it's the first message
        messages_count = supabase.table('messages').select('id', count='exact').eq('chat_id', current_chat['id']).execute()
        if messages_count.count == 1:
            title = user_message[:30] + "..." if len(user_message) > 30 else user_message
            if not title and image_data:
                title = f"Image: {image_data['filename']}"
            
            supabase.table('chats').update({
                'title': title,
                'updated_at': datetime.now().isoformat()
            }).eq('id', current_chat['id']).execute()
        
        # Two-step processing
        bot_message = "Sorry, I could not get a response from the AI service."
        final_query = user_message
        
        try:
            # STEP 1: If there's an image, send to image webhook first
            if image_data:
                print(f"🖼️ Step 1: Sending image to image webhook...")
                
                files = {
                    'image': (image_data['filename'], image_data['binary'], image_data['mime_type'])
                }
                
                image_payload = {
                    'message': user_message,
                    'conversation_history': json.dumps(conversation_history),
                    'chat_id': current_chat['id'],
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat(),
                    'context_message_count': len(conversation_history)
                }
                
                try:
                    image_response = requests.post(
                        N8N_IMAGE_WEBHOOK_URL,
                        files=files,
                        data=image_payload,
                        timeout=60
                    )
                    
                    print(f"📨 Image Webhook Response Status: {image_response.status_code}")
                    
                    if image_response.status_code == 200:
                        try:
                            image_response_text = image_response.text.strip()
                            
                            try:
                                image_response_data = image_response.json()
                            except json.JSONDecodeError:
                                final_query = image_response_text
                            else:
                                # Extract enhanced query
                                if isinstance(image_response_data, str):
                                    final_query = image_response_data
                                elif isinstance(image_response_data, list) and len(image_response_data) > 0:
                                    first_item = image_response_data[0]
                                    if isinstance(first_item, dict):
                                        final_query = (
                                            first_item.get('query') or
                                            first_item.get('enhanced_query') or
                                            first_item.get('output') or
                                            first_item.get('response') or
                                            first_item.get('message') or
                                            str(first_item)
                                        )
                                    else:
                                        final_query = str(first_item)
                                elif isinstance(image_response_data, dict):
                                    final_query = (
                                        image_response_data.get('query') or
                                        image_response_data.get('enhanced_query') or
                                        image_response_data.get('output') or
                                        image_response_data.get('response') or
                                        image_response_data.get('message') or
                                        str(image_response_data)
                                    )
                                
                                print(f"✅ Enhanced query: {final_query[:100]}...")
                                
                        except Exception as parse_error:
                            print(f"❌ Error parsing image webhook response: {parse_error}")
                            final_query = user_message
                            
                    else:
                        print(f"❌ Image webhook failed with status {image_response.status_code}")
                        final_query = user_message
                        
                except Exception as e:
                    print(f"❌ Image webhook error: {e}")
                    final_query = user_message
            
            # STEP 2: Send to main webhook
            print(f"🤖 Step 2: Sending {'enhanced' if image_data else 'original'} query to main webhook...")
            
            main_payload = {
                'message': final_query,
                'conversation_history': conversation_history,
                'chat_id': current_chat['id'],
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'context_message_count': len(conversation_history),
                'has_image': image_data is not None,
                'original_message': user_message if image_data else None
            }
            
            main_response = requests.post(
                N8N_WEBHOOK_URL,
                json=main_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            print(f"📨 Main Webhook Response Status: {main_response.status_code}")
            
            if main_response.status_code == 200:
                try:
                    main_response_text = main_response.text.strip()
                    
                    try:
                        main_response_data = main_response.json()
                    except json.JSONDecodeError:
                        bot_message = main_response_text
                    else:
                        # Extract final response
                        if isinstance(main_response_data, str):
                            bot_message = main_response_data
                        elif isinstance(main_response_data, list) and len(main_response_data) > 0:
                            first_item = main_response_data[0]
                            if isinstance(first_item, dict):
                                bot_message = (
                                    first_item.get('output') or
                                    first_item.get('response') or
                                    first_item.get('message') or 
                                    first_item.get('text') or
                                    first_item.get('result') or
                                    str(first_item)
                                )
                            else:
                                bot_message = str(first_item)
                        elif isinstance(main_response_data, dict):
                            bot_message = (
                                main_response_data.get('output') or
                                main_response_data.get('response') or
                                main_response_data.get('message') or 
                                main_response_data.get('text') or
                                main_response_data.get('result') or
                                str(main_response_data)
                            )
                        
                        if not bot_message:
                            bot_message = f'Received response but could not parse it: {str(main_response_data)[:200]}...'
                            
                except Exception as parse_error:
                    print(f"❌ Error processing main webhook response: {parse_error}")
                    bot_message = f'Error processing AI response: {str(parse_error)}'
                    
            else:
                print(f"❌ Main webhook returned status {main_response.status_code}")
                bot_message = f'AI service returned status {main_response.status_code}.'
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            bot_message = f'Unexpected error: {str(e)}'
        
        # Add bot response to database
        supabase.table('messages').insert({
            'chat_id': current_chat['id'],
            'role': 'assistant',
            'content': bot_message,
            'has_image': False
        }).execute()
        
        # Update chat's updated_at timestamp
        supabase.table('chats').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', current_chat['id']).execute()
        
        return jsonify({
            'user_message': user_message,
            'bot_response': bot_message,
            'chat_id': current_chat['id'],
            'has_image': stored_image_info is not None,
            'image_info': stored_image_info,
            'enhanced_query': final_query if image_data else None
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
        
        # Get messages for this chat
        messages_response = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at').execute()
        
        chat['messages'] = messages_response.data
        session['current_chat_id'] = chat_id
        
        print(f"📖 Loaded chat {chat_id} with {len(chat['messages'])} messages")
        
        return jsonify(chat)
        
    except Exception as e:
        print(f"❌ Error loading chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_chat_histories')
@login_required
def get_chat_histories_api():
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
    print(f"🚀 Starting Flask application...")
    print(f"🔧 Debug mode: {DEBUG}")
    print(f"🌐 Port: {PORT}")
    print(f"🔗 N8N Main Webhook: {N8N_WEBHOOK_URL}")
    print(f"🖼️ N8N Image Webhook: {N8N_IMAGE_WEBHOOK_URL}")
    print(f"🗄️ Supabase Connected: {'✅ Yes' if supabase else '❌ No'}")
    print(f"📱 Open: http://localhost:{PORT}")
    app.run(debug=DEBUG, port=PORT, host='127.0.0.1')