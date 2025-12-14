from flask import Blueprint, request, jsonify
from database import db
from models.stock import Stock
import yfinance as yf
from datetime import datetime

bp = Blueprint('prices', __name__)


@bp.route('/update/<string:symbol>', methods=['POST'])
def update_stock_price(symbol):
    """Update price for a specific stock"""
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404
    
    try:
        # Fetch stock data from yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price:
            stock.current_price = current_price
            stock.last_updated = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'symbol': stock.symbol,
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat()
            })
        else:
            return jsonify({'error': 'Could not fetch price for this stock'}), 500
            
    except Exception as e:
        error_msg = str(e)
        # Check for rate limiting
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return jsonify({'error': 'Rate limit reached. Please wait a few minutes before trying again.'}), 429
        elif 'HTTPError' in error_msg or 'Connection' in error_msg:
            return jsonify({'error': 'Unable to connect to price service. Please try again later.'}), 503
        else:
            return jsonify({'error': f'Failed to fetch stock price: {error_msg}'}), 500


@bp.route('/update-all', methods=['POST'])
def update_all_prices():
    """Update prices for all stocks in the database"""
    stocks = Stock.query.all()
    
    if not stocks:
        return jsonify({'message': 'No stocks to update'}), 200
    
    updated = []
    failed = []
    rate_limited = False
    
    for stock in stocks:
        try:
            ticker = yf.Ticker(stock.symbol)
            info = ticker.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price:
                stock.current_price = current_price
                stock.last_updated = datetime.utcnow()
                updated.append(stock.symbol)
            else:
                failed.append({'symbol': stock.symbol, 'error': 'Price not available'})
                
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'Too Many Requests' in error_msg:
                rate_limited = True
                failed.append({'symbol': stock.symbol, 'error': 'Rate limit reached'})
                # Stop trying if we hit rate limit
                break
            else:
                failed.append({'symbol': stock.symbol, 'error': error_msg})
    
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
