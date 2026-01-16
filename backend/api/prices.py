from flask import Blueprint, request, jsonify
from database import db
from models.stock import Stock
import yfinance as yf
from datetime import datetime, timedelta
import time

bp = Blueprint('prices', __name__)

# Simple cooldown tracker - prevents too frequent updates
last_update_times = {}
COOLDOWN_SECONDS = 60  # 1 minute cooldown between updates for same stock

def fetch_current_price(symbol: str):
    """Fetch the current stock price from Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if data.empty:
        raise RuntimeError("****** No data received from Yahoo Finance")
    # Get the last available close price
    current_price = data['Close'].iloc[-1]
    return round(current_price, 2)

@bp.route('/update/<string:symbol>', methods=['POST'])
def update_stock_price(symbol):
    """Update price for a specific stock"""
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404
    
    # Check if recently updated (within cooldown period)
    if stock.last_updated:
        time_since_update = datetime.utcnow() - stock.last_updated
        if time_since_update.total_seconds() < COOLDOWN_SECONDS:
            seconds_remaining = int(COOLDOWN_SECONDS - time_since_update.total_seconds())
            return jsonify({
                'error': f'Stock price was updated recently. Please wait {seconds_remaining} seconds.',
                'last_updated': stock.last_updated.isoformat(),
                'current_price': stock.current_price
            }), 429
    
    # Check global rate limit for this symbol
    symbol_key = symbol.upper()
    if symbol_key in last_update_times:
        time_since_last = time.time() - last_update_times[symbol_key]
        if time_since_last < COOLDOWN_SECONDS:
            return jsonify({
                'error': f'Please wait {int(COOLDOWN_SECONDS - time_since_last)} seconds before updating this stock again.',
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None,
                'current_price': stock.current_price
            }), 429
    
    try:
        current_price = fetch_current_price(symbol)
                   
        # If we got a price, update the database
        if current_price:
            stock.current_price = float(current_price)
            stock.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Update cooldown tracker
            last_update_times[symbol_key] = time.time()
            
            return jsonify({
                'symbol': stock.symbol,
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat()
            })
        else:
            return jsonify({
                'error': f'Could not fetch current price for {symbol}. The stock symbol may be invalid or temporarily unavailable.',
                'hint': 'Verify the symbol is correct for NSE stocks (e.g., RELIANCE.NS)',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            }), 404
            
    except Exception as e:
        error_msg = str(e)
        
        # Check for rate limiting
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                'error': 'Yahoo Finance rate limit reached. Please wait a few minutes before trying again.',
                'hint': 'Try refreshing individual stocks with longer intervals between requests.',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            }), 429
        elif 'HTTPError' in error_msg or 'Connection' in error_msg or 'Timeout' in error_msg:
            return jsonify({
                'error': 'Unable to connect to Yahoo Finance. Please check your internet connection and try again.',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            }), 503
        else:
            return jsonify({
                'error': f'Failed to fetch stock price: {error_msg}',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            }), 500


@bp.route('/update-all', methods=['POST'])
def update_all_prices():
    """Update prices for all stocks in the database"""
    stocks = Stock.query.all()
    
    if not stocks:
        return jsonify({'message': 'No stocks to update'}), 200
    
    updated = []
    failed = []
    rate_limited = False
    
    for i, stock in enumerate(stocks):
        # Add delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(1)  # 1 second delay between stocks
        
        try:
            ticker = yf.Ticker(stock.symbol)
            current_price = None
            
            # Try history method first
            try:
                hist = ticker.history(period='5d')
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            except:
                pass
            
            # Try fast_info method
            if not current_price:
                try:
                    current_price = ticker.fast_info.get('lastPrice')
                except:
                    pass
            
            # Try info method as last resort
            if not current_price:
                try:
                    info = ticker.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                except:
                    pass
            
            if current_price:
                stock.current_price = float(current_price)
                stock.last_updated = datetime.utcnow()
                updated.append(stock.symbol)
            else:
                failed.append({'symbol': stock.symbol, 'error': 'Price not available'})
                
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'Too Many Requests' in error_msg:
                rate_limited = True
                failed.append({'symbol': stock.symbol, 'error': 'Rate limit reached'})
                print(f"Rate limit hit at {stock.symbol}")
                # Stop trying if we hit rate limit
                break
            else:
                failed.append({'symbol': stock.symbol, 'error': error_msg})
                print(f"Error updating {stock.symbol}: {error_msg}")
    
    db.session.commit()
    
    response = {
        'updated': updated,
        'failed': failed,
        'updated_count': len(updated),
        'failed_count': len(failed)
    }
    
    if rate_limited:
        response['warning'] = 'Rate limit reached. Please wait a few minutes before updating remaining stocks.'
    
    return jsonify(response)


@bp.route('/fetch/<string:symbol>', methods=['GET'])
def fetch_stock_info(symbol):
    """Fetch stock information from yfinance without saving to database"""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        return jsonify({
            'symbol': symbol.upper(),
            'name': info.get('longName', info.get('shortName')),
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'exchange': info.get('exchange'),
            'sector': info.get('sector'),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency')
        })
        
    except Exception as e:
        error_msg = str(e)
        # Check for rate limiting
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return jsonify({'error': 'Rate limit reached. Please wait a few minutes before trying again.'}), 429
        elif 'HTTPError' in error_msg or 'Connection' in error_msg:
            return jsonify({'error': 'Unable to connect to price service. Please try again later.'}), 503
        else:
            return jsonify({'error': f'Failed to fetch stock info: {error_msg}'}), 500
