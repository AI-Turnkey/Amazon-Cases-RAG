from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

auth_bp = Blueprint('auth', __name__)

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Error initializing Supabase in auth: {e}")
    supabase = None

@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/signup', methods=['POST'])
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

@auth_bp.route('/logout')
def logout():
    try:
        if supabase:
            supabase.auth.sign_out()
    except Exception as e:
        print(f"Logout error: {e}")
    session.clear()
    return redirect(url_for('auth.login'))
