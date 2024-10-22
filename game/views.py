import os
import random
from django.shortcuts import render, redirect
from django.conf import settings
import yfinance as yf
from datetime import datetime, timedelta
from .models import StockSelection
from django.http import JsonResponse

def reset_game_view(request):
    request.session.flush()  # Clear all session data
    return redirect('stock_selection')  # Redirect to the stock selection page

def newspaper_view(request):
    print("Stock selection view called")

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

def stock_selection_view(request):
    # Initialize the user's money if it does not exist in the session
    if 'initialized' not in request.session:
        request.session['balance'] = 1000000.0  # $1,000,000 initial balance
        request.session['initialized'] = True

    if request.method == 'POST':
        stock_symbols = request.POST.getlist('stock_symbol')
        quantities = [int(q) for q in request.POST.getlist('quantity')]
        purchase_date = request.GET.get('purchase_date')

        total_cost = 0
        stock_details = []

        for i, stock_symbol in enumerate(stock_symbols):
            stock_symbol = stock_symbol.upper()
            quantity = quantities[i]

            # Fetch stock history
            stock = yf.Ticker(stock_symbol)
            hist = stock.history(period="max")

            # Format the date correctly
            try:
                formatted_date = datetime.strptime(purchase_date, '%Y_%m_%d').strftime('%Y-%m-%d')
            except ValueError:
                return render(request, 'game/stock_selection.html', {
                    'error': 'Invalid date format. Please use YYYY-MM-DD.',
                    'balance': round(request.session['balance'], 2),
                })

            # Check if the formatted date exists in the data
            if formatted_date not in hist.index:
                return render(request, 'game/stock_selection.html', {
                    'error': f'No data available for {stock_symbol} on the specified date.',
                    'balance': round(request.session['balance'], 2),
                })

            purchase_price = hist.loc[formatted_date]['Open']
            total_cost += purchase_price * quantity

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

            # Calculate profit or loss
            if future_price is not None:
                profit_loss = (future_price - purchase_price) * quantity
            else:
                profit_loss = None

            # Store stock details for later use
            stock_details.append({
                'symbol': stock_symbol,
                'quantity': quantity,
                'purchase_price': round(purchase_price, 2),
                'future_price': round(future_price, 2) if future_price else None,
                'profit_loss': round(profit_loss, 2) if profit_loss is not None else None,
            })

        # Check if the user has enough money
        if total_cost > request.session['balance']:
            return render(request, 'game/stock_selection.html', {
                'error': 'Insufficient funds for this purchase.',
                'balance': round(request.session['balance'], 2),
            })
        

        # Deduct the total amount from the session balance
        request.session['balance'] -= total_cost

        # Save the updated balance
        request.session.modified = True

        return render(request, 'game/results.html', {
            'stock_details': stock_details,
            'balance': round(request.session['balance'], 2),
        })
        

    else:
        return render(request, 'game/stock_selection.html', {
            'balance': round(request.session['balance'], 2),
        })
    
    
def get_price(request):
    stock_symbol = request.GET.get('stock_symbol')
    purchase_date = request.GET.get('purchase_date')
    
    try:
        # Fetch stock data from Yahoo Finance
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period="max")
        
        formatted_date = datetime.strptime(purchase_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        if formatted_date in hist.index:
            price = hist.loc[formatted_date]['Open']
            return JsonResponse({'price': price})
        else:
            return JsonResponse({'error': 'No price data available'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    # Retrieve the stock selection data from the session
    stock_selection = request.session.get('stock_selection')
    if stock_selection:
        # Context with all necessary details
        context = {
            'stock_symbol': stock_selection['stock_symbol'],
            'purchase_date': stock_selection['purchase_date'],
            'quantity': stock_selection['quantity'],
            'purchase_price': stock_selection['purchase_price'],
            'future_price': stock_selection['future_price'],
            'profit_loss': stock_selection['profit_loss'],
            'balance': request.session.get('balance'),
        }
        return render(request, 'game/results.html', context)
    else:
        return render(request, 'game/results.html', {'error': 'No selections made.'})