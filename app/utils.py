import os
import uuid
from datetime import datetime, timedelta
from supabase import create_client
from config import (
    SUPABASE_URL, 
    SUPABASE_KEY, 
    MAX_MESSAGES_PER_CHAT, 
    MAX_TOTAL_CHATS_PER_USER,
    MESSAGE_CONTEXT_LIMIT
)

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Error initializing Supabase in utils: {e}")
    supabase = None

def generate_unique_filename(original_filename):
    """Generate a unique filename for uploaded files"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    return f"chat_image_{uuid.uuid4()}.{ext}"

def get_conversation_context(chat_id, limit=MESSAGE_CONTEXT_LIMIT):
    """Get recent conversation context for AI processing"""
    if not supabase:
        return ""
    
    try:
        messages_response = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at', desc=True).limit(limit).execute()
        
        conversation_context = []
        for msg in reversed(messages_response.data):
            role = "User" if msg['role'] == 'user' else "Assistant"
            conversation_context.append(f"{role}: {msg['content']}")
        
        return "\n".join(conversation_context)
    except Exception as e:
        print(f"❌ Error getting conversation context: {e}")
        return ""

def cleanup_user_data(user_id):
    """Comprehensive cleanup of user data"""
    if not supabase:
        return False
    
    try:
        # Get all user chats
        all_chats = supabase.table('chats').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
        
        if len(all_chats.data) > MAX_TOTAL_CHATS_PER_USER:
            # Keep only the most recent chats
            chats_to_keep = all_chats.data[:MAX_TOTAL_CHATS_PER_USER]
            chats_to_delete = all_chats.data[MAX_TOTAL_CHATS_PER_USER:]
            
            for chat in chats_to_delete:
                delete_chat_completely(chat['id'])
            
            print(f"🧹 Cleaned up {len(chats_to_delete)} old chats for user {user_id}")
        
        # Clean up messages in remaining chats
        for chat in all_chats.data[:MAX_TOTAL_CHATS_PER_USER]:
            cleanup_chat_messages(chat['id'])
        
        return True
    except Exception as e:
        print(f"❌ Error in cleanup_user_data: {e}")
        return False

def delete_chat_completely(chat_id):
    """Completely delete a chat and all associated data"""
    if not supabase:
        return False
    
    try:
        # Get messages with images
        messages_with_images = supabase.table('messages').select('*').eq('chat_id', chat_id).eq('has_image', True).execute()
        
        # Delete images from storage
        for message in messages_with_images.data:
            if message.get('image_url'):
                try:
                    filename = message['image_url'].split('/')[-1]
                    supabase.storage.from_("chat-images").remove([filename])
                except Exception:
                    pass  # Continue even if image deletion fails
        
        # Delete all messages in the chat
        supabase.table('messages').delete().eq('chat_id', chat_id).execute()
        
        # Delete the chat
        supabase.table('chats').delete().eq('id', chat_id).execute()
        
        return True
    except Exception as e:
        print(f"❌ Error in delete_chat_completely: {e}")
        return False
