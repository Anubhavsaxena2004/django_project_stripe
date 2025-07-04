from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from api.models import Prediction
from django.conf import settings
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from sklearn.metrics import mean_squared_error, r2_score
import os
from api.utils import save_plot

class Command(BaseCommand):
    help = 'Run stock price prediction for a ticker or all tickers.'

    def add_arguments(self, parser):
        parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
        parser.add_argument('--all', action='store_true', help='Predict for all tickers in the database')
        parser.add_argument('--user', type=str, help='Username to associate predictions with (required)')

    def handle(self, *args, **options):
        ticker = options.get('ticker')
        all_flag = options.get('all')
        username = options.get('user')
        if not username:
            raise CommandError('You must provide a --user argument (username to associate predictions with).')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User {username} does not exist.')
        tickers = []
        if all_flag:
            # Example: get all tickers from a list or database
            tickers = ['AAPL', 'TSLA', 'GOOG']  # Replace with your logic
        elif ticker:
            tickers = [ticker]
        else:
            raise CommandError('Provide --ticker or --all.')
        model_path = getattr(settings, 'MODEL_PATH', 'stock_prediction_model.keras')
        if not os.path.exists(model_path):
            raise CommandError('Model file not found.')
        model = load_model(model_path)
        for t in tickers:
            self.stdout.write(f'Predicting for {t}...')
            try:
                now = datetime.now()
                start = datetime(now.year-10, now.month, now.day)
                end = now
                df = yf.download(t, start, end)
                if df.empty:
                    self.stdout.write(self.style.ERROR(f'No data for {t}'))
                    continue
                df = df.reset_index()
                # Plot 1: Closing price history
                plt.switch_backend('AGG')
                plt.figure(figsize=(12, 5))
                plt.plot(df.Close, label='Closing Price')
                plt.title(f'Closing price of {t}')
                plt.xlabel('Days')
                plt.ylabel('Price')
                plt.legend()
                plot_history = save_plot(f'{t}_history.png')
                # Split data
                data_training = pd.DataFrame(df.Close[0:int(len(df)*0.7)])
                data_testing = pd.DataFrame(df.Close[int(len(df)*0.7): int(len(df))])
                scaler = MinMaxScaler(feature_range=(0,1))
                data_training_array = scaler.fit_transform(data_training)
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
                plt.title(f'Actual vs Predicted for {t}')
                plt.xlabel('Days')
                plt.ylabel('Price')
                plt.legend()
                plot_prediction = save_plot(f'{t}_prediction.png')
                # Metrics
                mse = float(mean_squared_error(y_test, y_predicted))
                rmse = float(np.sqrt(mse))
                r2 = float(r2_score(y_test, y_predicted))
                next_day_price = float(y_predicted[-1]) if len(y_predicted) > 0 else None
                Prediction.objects.create(
                    user=user,
                    ticker=t,
                    next_day_price=next_day_price,
                    metrics={'mse': mse, 'rmse': rmse, 'r2': r2},
                    plot_urls=[plot_history, plot_prediction]
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully predicted for {t}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error for {t}: {e}')) 