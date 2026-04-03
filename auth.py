#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth Authentication Handler
Manages login/logout for 3 admin users
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', '').split(',')
ADMIN_EMAILS = [email.strip() for email in ADMIN_EMAILS if email.strip()]

class GoogleOAuth:
    """Handle Google OAuth authentication"""
    
    @staticmethod
    def verify_token(token):
        """Verify Google ID token and return user info"""
        try:
            if not GOOGLE_CLIENT_ID:
                print("❌ ERROR: GOOGLE_CLIENT_ID not set in .env")
                return None
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'google_id': idinfo.get('sub'),
                'verified_email': idinfo.get('email_verified')
            }
        
        except ValueError:
            # Invalid token
            print("❌ Invalid token")
            return None
        except Exception as e:
            print(f"❌ Error verifying token: {e}")
            return None
    
    @staticmethod
    def is_admin(email):
        """Check if email is in admin whitelist"""
        return email in ADMIN_EMAILS
    
    @staticmethod
    def set_session(user_info):
        """Set user session after successful login"""
        session['user_email'] = user_info['email']
        session['user_name'] = user_info['name']
        session['user_picture'] = user_info['picture']
        session['google_id'] = user_info['google_id']
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True
        session.modified = True
    
    @staticmethod
    def get_session_user():
        """Get current user from session"""
        if 'user_email' in session:
            return {
                'email': session.get('user_email'),
                'name': session.get('user_name'),
                'picture': session.get('user_picture'),
                'google_id': session.get('google_id')
            }
        return None
    
    @staticmethod
    def clear_session():
        """Clear user session (logout)"""
        session.clear()


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = GoogleOAuth.get_session_user()
        if not user:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = GoogleOAuth.get_session_user()
        if not user:
            return redirect(url_for('login'))
        if not GoogleOAuth.is_admin(user['email']):
            return {"status": "error", "message": "Not authorized"}, 403
        return f(*args, **kwargs)
    return decorated_function


# Configuration info for setup
OAUTH_SETUP_INFO = {
    "title": "Google OAuth Setup",
    "steps": [
        {
            "step": 1,
            "title": "Create Google Cloud Project",
            "instructions": [
                "1. Go to https://console.cloud.google.com/",
                "2. Create new project",
                "3. Name it: 'Muller App'",
                "4. Click 'Create'"
            ]
        },
        {
            "step": 2,
            "title": "Enable OAuth 2.0",
            "instructions": [
                "1. Go to 'APIs & Services' > 'Credentials'",
                "2. Click 'Create Credentials' > 'OAuth 2.0 Client ID'",
                "3. Choose 'Web application'",
                "4. Name: 'Muller App Web Client'"
            ]
        },
        {
            "step": 3,
            "title": "Configure Redirect URIs",
            "instructions": [
                "Add Authorized redirect URIs:",
                "- http://localhost:5000/auth/callback",
                "- https://your-vercel-domain.vercel.app/auth/callback"
            ]
        },
        {
            "step": 4,
            "title": "Copy Credentials",
            "instructions": [
                "Copy the credentials:",
                "- Client ID",
                "- Client Secret"
            ]
        },
        {
            "step": 5,
            "title": "Add to .env file",
            "instructions": [
                "GOOGLE_CLIENT_ID=your_client_id_here",
                "GOOGLE_CLIENT_SECRET=your_client_secret_here",
                "ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com"
            ]
        }
    ]
}
