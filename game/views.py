import os
import random
from django.shortcuts import render, redirect
from django.conf import settings
import yfinance as yf
from datetime import datetime, timedelta
from .models import StockSelection

def newspaper_view(request):
    newspaper_dir = os.path.join(settings.MEDIA_ROOT, 'newspapers')
    
    # Check if the directory exists and contains files
    if not os.path.exists(newspaper_dir):
        os.makedirs(newspaper_dir)
    
    newspapers = os.listdir(newspaper_dir)
    
    # If there are no newspapers, handle it gracefully
    if not newspapers:
        return render(request, 'game/no_newspapers.html')
    
    selected_newspaper = random.choice(newspapers)
    context = {
        'newspaper_image': f'newspapers/{selected_newspaper}',
        'purchase_date': os.path.splitext(selected_newspaper)[0],  # Extract date from filename
        'media_url': settings.MEDIA_URL  # Pass MEDIA_URL explicitly to the context
    }
    return render(request, 'game/newspaper.html', context)

from django.shortcuts import render
import yfinance as yf
from datetime import datetime, timedelta

def stock_selection_view(request):
    # Initialize the user's money if it does not exist in the session
    if 'balance' not in request.session:
        request.session['balance'] = 1000000  # $1,000,000 initial balance

    if request.method == 'POST':
        stock_symbol = request.POST.get('stock_symbol').upper()
        quantity = int(request.POST.get('quantity'))
        purchase_date = request.POST.get('purchase_date')

        # Convert the purchase_date from 'YYYY_MM_DD' to 'YYYY-MM-DD'
        try:
            formatted_date = datetime.strptime(purchase_date, '%Y_%m_%d').strftime('%Y-%m-%d')
        except ValueError:
            return render(request, 'game/stock_selection.html', {
                'error': 'Invalid date format. Please use YYYY-MM-DD.',
                'purchase_date': purchase_date,
            })

        # Fetch stock history with maximum range
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period="max")

        # Check if the date exists in the historical data
        if formatted_date not in hist.index:
            return render(request, 'game/stock_selection.html', {
                'error': 'No data available for that stock on the specified date.',
                'purchase_date': purchase_date,
            })

        specific_day_data = hist.loc[formatted_date]

        # Fetch the open price on the purchase date
        purchase_price = specific_day_data['Open']
        print(f"\nPrice at open: {purchase_price}")

        # Calculate the total purchase cost
        total_cost = purchase_price * quantity

        # Check if the user has enough money
        if total_cost > request.session['balance']:
            return render(request, 'game/stock_selection.html', {
                'error': 'Insufficient funds for this purchase.',
                'purchase_date': purchase_date,
                'balance': request.session['balance'],
            })

        # Deduct the amount from the session balance
        request.session['balance'] -= total_cost

        # Calculate the date two weeks later
        two_weeks_later = datetime.strptime(formatted_date, '%Y-%m-%d') + timedelta(weeks=2)
        two_weeks_later_str = two_weeks_later.strftime('%Y-%m-%d')

        # Find the nearest trading date for the future price
        future_price = None
        if two_weeks_later_str in hist.index:
            future_price = hist.loc[two_weeks_later_str]['Open']
        else:
            # Look for the nearest available trading day within a 5-day range
            for offset in range(1, 6):
                future_date = two_weeks_later + timedelta(days=offset)
                future_date_str = future_date.strftime('%Y-%m-%d')
                if future_date_str in hist.index:
                    future_price = hist.loc[future_date_str]['Open']
                    break

        print(f"\nPrice 2 weeks later: {future_price}")

        # Calculate profit or loss
        if future_price is not None:
            profit_loss = (future_price - purchase_price) * quantity
            request.session['balance'] += profit_loss  # Update balance with the profit or loss
        else:
            profit_loss = None

        # Save the selection in the session
        request.session['stock_selection'] = {
            'stock_symbol': stock_symbol,
            'purchase_date': formatted_date,
            'purchase_price': purchase_price,
            'future_price': future_price,
            'profit_loss': profit_loss,
        }

        return render(request, 'game/results.html', {
            'stock_symbol': stock_symbol,
            'purchase_date': formatted_date,
            'purchase_price': purchase_price,
            'future_price': future_price,
            'profit_loss': profit_loss,
            'balance': request.session['balance'],
        })

    else:
        purchase_date = request.GET.get('purchase_date')
        return render(request, 'game/stock_selection.html', {
            'purchase_date': purchase_date,
            'balance': request.session['balance'],
        })

def get_price_on_date(stock_symbol, date_str):
    """Fetches the closing price for the stock on or near the given date."""
    stock = yf.Ticker(stock_symbol)
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    for offset in range(6):  # Check up to 5 days ahead
        future_date_str = (date + timedelta(days=offset)).strftime('%Y-%m-%d')
        hist = stock.history(start=future_date_str, end=future_date_str)

        if not hist.empty:
            return hist['Close'].iloc[0]
    return None

def results_view(request):
    # Assuming you store stock selection data in the session instead of database
    stock_selection = request.session.get('stock_selection')
    if stock_selection:
        context = {
            'stock_symbol': stock_selection.get('stock_symbol'),
            'purchase_date': stock_selection.get('purchase_date'),
            'quantity': stock_selection.get('quantity'),  # Ensure this is stored in the session
            'purchase_price': stock_selection.get('purchase_price'),
            'future_price': stock_selection.get('future_price'),
            'profit_loss': stock_selection.get('profit_loss'),
            'balance': request.session.get('balance'),
        }
        return render(request, 'game/results.html', context)
    else:
        return render(request, 'game/results.html', {'error': 'No selections made.'})