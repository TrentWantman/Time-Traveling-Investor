import yfinance as yf
from datetime import datetime

# Function to test historical data retrieval
def test_stock_data(stock_symbol, purchase_date):
    # Convert the purchase_date from 'YYYY_MM_DD' to 'YYYY-MM-DD'
    formatted_date = datetime.strptime(purchase_date, '%Y_%m_%d').strftime('%Y-%m-%d')
    
    # Get the ticker object
    stock = yf.Ticker(stock_symbol)

    # Print general stock info
    print(f"Fetching data for: {stock_symbol}")
    print("Stock Info:", stock.info)
    print("\n")

    # Get historical market data for 1 month around the purchase date
    print("Fetching historical data for the past 1 month...")
    hist = stock.history(period="max")

    # Print the historical data
    print("\nHistorical Data (1 month):")
    print(hist)

    # Print the history metadata to verify date ranges
    print("\nHistory Metadata:")
    print(stock.history_metadata)

    # Filter the data for the specific date
    if formatted_date in hist.index:
        specific_day_data = hist.loc[formatted_date]
        print(f"\nData for {formatted_date}:")
        print(specific_day_data['Open'])
    else:
        print(f"\nNo data available for the exact date: {formatted_date}")

# Run the tester with a sample stock and date
if __name__ == "__main__":
    test_stock_data("AAPL", "2008_08_06")
