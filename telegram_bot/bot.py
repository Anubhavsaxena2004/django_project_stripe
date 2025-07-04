import os
import django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_prediction_main.settings')
django.setup()
from api.models import TelegramUser, User, Prediction
from django.db import IntegrityError
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from api.utils import save_plot
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from django.conf import settings
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error, r2_score
from asgiref.sync import sync_to_async

BOT_TOKEN = os.environ.get('BOT_TOKEN')
LINKING, = range(1)

TELEGRAM_UPGRADE_URL = os.environ.get('TELEGRAM_UPGRADE_URL', 'https://localhost:8000/subscribe/')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Check if already linked
    if await sync_to_async(TelegramUser.objects.filter(chat_id=chat_id).exists)():
        await update.message.reply_text('Your Telegram account is already linked.')
        return
    await update.message.reply_text('Welcome to Stock Insight Bot! Please reply with your web username to link your account.')
    return LINKING

async def link_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.message.text.strip()
    try:
        user = await sync_to_async(User.objects.get)(username=username)
        await sync_to_async(TelegramUser.objects.create)(user=user, chat_id=chat_id)
        await update.message.reply_text('Your Telegram account has been linked! You can now use /predict <TICKER> and /latest.')
        return ConversationHandler.END
    except User.DoesNotExist:
        await update.message.reply_text('Username not found. Please try again.')
        return LINKING
    except IntegrityError:
        await update.message.reply_text('This Telegram account is already linked.')
        return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Commands:\n/predict <TICKER> - Predict next day price\n/latest - Your last prediction\n/help - Show this message')

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text('Usage: /predict <TICKER>')
        return
    ticker = context.args[0].upper()
    try:
        telegram_user = await sync_to_async(TelegramUser.objects.get)(chat_id=chat_id)
        profile = await sync_to_async(lambda: telegram_user.user.userprofile)()
        from django.utils import timezone
        today = timezone.now().date()
        count = await sync_to_async(Prediction.objects.filter(user=telegram_user.user, created__date=today).count)()
        if not profile.is_pro and count >= 5:
            await update.message.reply_text(
                f'Free tier: 5 predictions/day limit reached. Upgrade to Pro for unlimited predictions: {TELEGRAM_UPGRADE_URL}'
            )
            return
    except TelegramUser.DoesNotExist:
        await update.message.reply_text('Please link your account first using /start.')
        return
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
        return
    try:
        now = datetime.now()
        start = datetime(now.year-10, now.month, now.day)
        end = now
        df = yf.download(ticker, start, end)
        if df.empty:
            await update.message.reply_text('No data found for the given ticker.')
            return
        df = df.reset_index()
        # Plot 1: Closing price history
        plt.switch_backend('AGG')
        plt.figure(figsize=(12, 5))
        plt.plot(df.Close, label='Closing Price')
        plt.title(f'Closing price of {ticker}')
        plt.xlabel('Days')
        plt.ylabel('Price')
        plt.legend()
        plot_history = save_plot(f'{ticker}_history.png')
        # Split data
        data_training = pd.DataFrame(df.Close[0:int(len(df)*0.7)])
        data_testing = pd.DataFrame(df.Close[int(len(df)*0.7): int(len(df))])
        scaler = MinMaxScaler(feature_range=(0,1))
        data_training_array = scaler.fit_transform(data_training)
        # Load model
        model_path = getattr(settings, 'MODEL_PATH', 'stock_prediction_model.keras')
        if not os.path.exists(model_path):
            await update.message.reply_text('Model file not found.')
            return
        model = load_model(model_path)
        # Prepare test data
        past_100_days = data_training.tail(100)
        final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
        input_data = scaler.transform(final_df)
        x_test = []
        y_test = []
        for i in range(100, input_data.shape[0]):
            x_test.append(input_data[i-100: i])
            y_test.append(input_data[i, 0])
        x_test, y_test = np.array(x_test), np.array(y_test)
        # Predict
        y_predicted = model.predict(x_test)
        y_predicted = scaler.inverse_transform(y_predicted.reshape(-1, 1)).flatten()
        y_test = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        # Plot 2: Actual vs predicted
        plt.switch_backend('AGG')
        plt.figure(figsize=(12, 5))
        plt.plot(y_test, 'b', label='Actual Price')
        plt.plot(y_predicted, 'r', label='Predicted Price')
        plt.title(f'Actual vs Predicted for {ticker}')
        plt.xlabel('Days')
        plt.ylabel('Price')
        plt.legend()
        plot_prediction = save_plot(f'{ticker}_prediction.png')
        # Metrics
        mse = float(mean_squared_error(y_test, y_predicted))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, y_predicted))
        next_day_price = float(y_predicted[-1]) if len(y_predicted) > 0 else None
        # Store prediction
        prediction = Prediction.objects.create(
            user=telegram_user.user,
            ticker=ticker,
            next_day_price=next_day_price,
            metrics={'mse': mse, 'rmse': rmse, 'r2': r2},
            plot_urls=[plot_history, plot_prediction]
        )
        await update.message.reply_text(f'Prediction for {ticker}: {next_day_price}\nMSE: {mse}\nRMSE: {rmse}\nR²: {r2}')
        # Send plots
        for url in [plot_history, plot_prediction]:
            plot_path = os.path.join(os.environ.get('MEDIA_ROOT', 'media'), os.path.basename(url))
            if os.path.exists(plot_path):
                with open(plot_path, 'rb') as img:
                    await update.message.reply_photo(photo=img)
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        telegram_user = await sync_to_async(TelegramUser.objects.get)(chat_id=chat_id)
        prediction = await sync_to_async(lambda: Prediction.objects.filter(user=telegram_user.user).order_by('-created').first())()
        if prediction:
            await update.message.reply_text(f'Latest prediction for {prediction.ticker}: {prediction.next_day_price}\nMSE: {prediction.metrics.get("mse")}\nRMSE: {prediction.metrics.get("rmse")}\nR²: {prediction.metrics.get("r2")}')
            # Optionally send plot images
            for url in prediction.plot_urls:
                plot_path = os.path.join(os.environ.get('MEDIA_ROOT', 'media'), os.path.basename(url))
                if os.path.exists(plot_path):
                    with open(plot_path, 'rb') as img:
                        await update.message.reply_photo(photo=img)
        else:
            await update.message.reply_text('No predictions found.')
    except TelegramUser.DoesNotExist:
        await update.message.reply_text('Please link your account first using /start.')

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Upgrade to Pro for unlimited predictions: {TELEGRAM_UPGRADE_URL}')

def run_telegram_bot():
    if not BOT_TOKEN:
        print('BOT_TOKEN not set in environment variables.')
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LINKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_username)],
        },
        fallbacks=[CommandHandler('help', help_command)],
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('predict', predict_command))
    app.add_handler(CommandHandler('latest', latest_command))
    app.add_handler(CommandHandler('subscribe', subscribe_command))
    print('Telegram bot is running...')
    app.run_polling() 