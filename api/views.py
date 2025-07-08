from django.shortcuts import render, redirect
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .models import Prediction
from .serializers import UserRegisterSerializer, PredictionSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .utils import save_plot
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from django.conf import settings
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import stripe
from django.core.paginator import Paginator
from .models import UserProfile
from django.views import View
from rest_framework.permissions import IsAuthenticated

# Create your views here.

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID', 'price_1Rh3TA2cJFqwZzBWPfWDek9s')  # Replace with your test price ID

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class PredictionCreateView(generics.CreateAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Add a global cache for the model
    _model_cache = None

    def create(self, request, *args, **kwargs):
        ticker = request.data.get('ticker')
        if not ticker:
            return Response({'error': 'Ticker is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            now = datetime.now()
            start = datetime(now.year-10, now.month, now.day)
            end = now
            df = yf.download(ticker, start, end)
            if df.empty:
                return Response({'error': 'No data found for the given ticker.'}, status=status.HTTP_404_NOT_FOUND)
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
            # Lazy-load model
            model_path = getattr(settings, 'MODEL_PATH', 'stock_prediction_model.keras')
            if not os.path.exists(model_path):
                return Response({'error': 'Model file not found.'}, status=500)
            if PredictionCreateView._model_cache is None:
                from tensorflow.keras.models import load_model
                PredictionCreateView._model_cache = load_model(model_path)
            model = PredictionCreateView._model_cache
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
            # Next day price (last prediction)
            next_day_price = float(y_predicted[-1]) if len(y_predicted) > 0 else None
            # Store prediction
            prediction = Prediction.objects.create(
                user=request.user,
                ticker=ticker,
                next_day_price=next_day_price,
                metrics={'mse': mse, 'rmse': rmse, 'r2': r2},
                plot_urls=[plot_history, plot_prediction]
            )
            serializer = self.get_serializer(prediction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        
        def api_predict(self, request, *args, **kwargs):
            return self.create(request, *args, **kwargs)

class PredictionListView(generics.ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Prediction.objects.filter(user=self.request.user)
        ticker = self.request.query_params.get('ticker')
        date = self.request.query_params.get('date')
        if ticker:
            queryset = queryset.filter(ticker__iexact=ticker)
        if date:
            queryset = queryset.filter(created__date=date)
        return queryset

# Registration view
class RegisterTemplateView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return render(request, 'registration/register.html')
    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not username or not password:
            return render(request, 'registration/register.html', {'error': 'Username and password required.'})
        if User.objects.filter(username=username).exists():
            return render(request, 'registration/register.html', {'error': 'Username already exists.'})
        user = User.objects.create_user(username=username, email=email, password=password)
        # Do not log in the user automatically after registration
        return redirect('login')

# Login view
class LoginTemplateView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return render(request, 'registration/login.html')
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials.'})

# Dashboard view
class DashboardView(View):
    @method_decorator(login_required)
    def get(self, request):
        predictions = Prediction.objects.filter(user=request.user).order_by('-created')
        page_number = request.GET.get('page', 1)
        paginator = Paginator(predictions, 10)
        page_obj = paginator.get_page(page_number)
        return render(request, 'dashboard.html', {
            'predictions': page_obj.object_list,
            'page_obj': page_obj,
            'paginator': paginator,
        })

# Logout view
class LogoutView(View):
    @method_decorator(login_required)
    def get(self, request):
        logout(request)
        return redirect('login')

@login_required
def subscribe(request):
    user = request.user
    profile = user.userprofile
    if profile.is_pro:
        return redirect('dashboard')
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer_email=user.email,
        line_items=[{
            'price': STRIPE_PRICE_ID,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri('/') + '?subscribed=1',
        cancel_url=request.build_absolute_uri('/') + '?canceled=1',
        metadata={'user_id': user.id},
    )
    return redirect(session.url)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return HttpResponse(status=400)
    # Handle subscription events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        try:
            user = User.objects.get(id=user_id)
            profile = user.userprofile
            profile.is_pro = True
            profile.stripe_customer_id = session.get('customer')
            profile.stripe_subscription_id = session.get('subscription')
            profile.save()
        except Exception:
            pass
    elif event['type'] == 'customer.subscription.deleted':
        # Downgrade user if subscription canceled
        customer_id = event['data']['object']['customer']
        try:
            profile = UserProfile.objects.get(stripe_customer_id=customer_id)
            profile.is_pro = False
            profile.save()
        except Exception:
            pass
    return HttpResponse(status=200)

class predictionCreateView1(generics.CreateAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        predictions = Prediction.objects.all().order_by('-created')[:5]
        return JsonResponse({
            'predictions': PredictionSerializer(predictions, many=True).data
        }, status=200)
