# Stock Prediction Platform

A web application for stock price prediction using Django, REST API, and machine learning. Users can register, log in, make predictions, and view results with visualizations. Includes JWT authentication, Stripe integration, and Telegram bot support.

---

## Features
- User registration and authentication (JWT)
- Stock price prediction using a trained ML model
- Interactive dashboard with prediction history and plots
- Daily prediction quota for free users; unlimited for Pro
- Stripe payments for Pro upgrade
- Telegram bot integration

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

### 2. Set Up Python Environment
It's recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root. Example:
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
JWT_ACCESS_LIFETIME=15
JWT_REFRESH_LIFETIME=1440
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_PRICE_ID=price_your_stripe_price_id
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
BOT_TOKEN=your_telegram_bot_token
TELEGRAM_UPGRADE_URL=https://localhost:8000/subscribe/
MEDIA_ROOT=media
```
- For production, set `DEBUG=False` and update `ALLOWED_HOSTS` accordingly.
- If deploying on Railway, use PostgreSQL and set `DATABASE_URL` as provided by Railway.

### 5. Database Setup
Run migrations:
```bash
python manage.py migrate
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```
Visit [http://localhost:8000](http://localhost:8000) in your browser.

---

## Deployment

### Railway (Recommended)
- Add required environment variables in the Railway dashboard.
- Use the provided PostgreSQL plugin for production database.
- Make sure `MEDIA_ROOT` is set to a writable directory (e.g., `/tmp/media`).
- The app is configured to use Gunicorn for production.

### Docker
Build and run the container:
```bash
docker build -t stock-prediction .
docker run -p 8000:8000 --env-file .env stock-prediction
```

---

## Stripe Integration
- Set your Stripe keys in the `.env` file.
- Update the price ID and webhook secret as needed.

---

## Telegram Bot
- Set your bot token in the `.env` file.
- The bot can be started via Django management command or as a separate process.

---

## Troubleshooting
- **502/504 errors on Railway:** Check `ALLOWED_HOSTS`, `DATABASE_URL`, and that all migrations have run.
- **Static/media files not loading:** Ensure `MEDIA_ROOT` is writable and correctly set.
- **JWT errors:** Confirm JWT settings and that the user is authenticated.
- **Database errors:** For production, use PostgreSQL. For local testing, SQLite is fine.
- **Stripe issues:** Double-check your keys and webhook configuration.

---

## License
This project is for educational purposes. See `LICENSE` for details. 