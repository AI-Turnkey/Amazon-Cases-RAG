import os
from datetime import timedelta

# Environment variables for Railway deployment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ffreghtmxscuwfnjvlzz.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmcmVnaHRteHNjdXdmbmp2bHp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI5NDY4NzYsImV4cCI6MjA3ODUyMjg3Nn0.eYRvMInQqUtiWtUcHUAWi4cBk_J1HTvm8ilG4I4_r9s")

# N8N Webhook Configuration
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "https://turnkeyproductmanagement.app.n8n.cloud/webhook/9863887b-d65c-47d4-9100-1dad669dfce8")
N8N_IMAGE_WEBHOOK_URL = os.environ.get("N8N_IMAGE_WEBHOOK_URL", "https://your-n8n-instance.com/webhook/your-image-webhook")

# Flask Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production-railway-2024")
DEBUG = os.environ.get("DEBUG", "False").lower() in ['true', '1', 'yes']
PORT = int(os.environ.get("PORT", 5000))

# Chat Settings - Optimized for performance
MAX_CHAT_HISTORIES = int(os.environ.get("MAX_CHAT_HISTORIES", 50))  # Reduced from 50 to 10
MAX_MESSAGES_PER_CHAT = int(os.environ.get("MAX_MESSAGES_PER_CHAT", 10000))  # Limit messages per chat
MESSAGE_CONTEXT_LIMIT = int(os.environ.get("MESSAGE_CONTEXT_LIMIT", 50))  # Only send last 10 messages as context


# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# File upload settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Performance settings
DATABASE_CLEANUP_INTERVAL = int(os.environ.get("DATABASE_CLEANUP_INTERVAL", 2400))  # Hours between cleanup
MAX_TOTAL_CHATS_PER_USER = int(os.environ.get("MAX_TOTAL_CHATS_PER_USER", 2000))  # Total chats per user

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
