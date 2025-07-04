#!/usr/bin/env python3
"""
Script to create .env file with environment variables
"""
import os
import secrets

def generate_secret_key():
    """Generate a Django secret key"""
    return secrets.token_urlsafe(50)

def create_env_file():
    """Create .env file with environment variables"""
    env_content = f"""# Django Settings
SECRET_KEY={generate_secret_key()}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# JWT Settings
JWT_ACCESS_LIFETIME=15
JWT_REFRESH_LIFETIME=1440

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key_here
STRIPE_PRICE_ID=price_your_stripe_price_id_here
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret_here

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_UPGRADE_URL=https://localhost:8000/subscribe/

# Media Configuration
MEDIA_ROOT=/tmp/media
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print("⚠️  Remember to update the placeholder values with your actual credentials")

if __name__ == "__main__":
    create_env_file() 