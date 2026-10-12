from flask import Blueprint, request, jsonify, current_app
from database import db
from models.stock import Stock
import yfinance as yf
from datetime import datetime, timedelta
import time
import requests

bp = Blueprint('prices', __name__)

# Simple cooldown tracker - prevents too frequent updates
last_update_times = {}
COOLDOWN_SECONDS = 60  # 1 minute cooldown between updates for same stock

# Exchanges whose stocks are priced in INR (i.e. eligible for NSE bhavcopy sync)
_INR_EXCHANGES = {'NSE', 'BSE'}


def _base_symbol(symbol: str) -> str:
    """Upper-case a symbol and strip Yahoo exchange suffixes (.NS/.BO).

    Bhavcopy uses plain NSE codes (RELIANCE) while the DB stores Yahoo-style
    symbols (RELIANCE.NS), so both sides are compared on the base symbol.
    """
    sym = (symbol or '').strip().upper()
    for suffix in ('.NS', '.BO'):
        if sym.endswith(suffix):
            return sym[: -len(suffix)]
    return sym


def _is_inr_stock(stock: Stock) -> bool:
    """True when the stock's price is denominated in INR."""
    if (stock.currency or '').upper() == 'INR':
        return True
    return (stock.exchange or '').upper() in _INR_EXCHANGES


def _is_nse_stock(stock: Stock) -> bool:
    """True when the stock is listed on NSE (safe to apply NSE bhavcopy)."""
    exchange = (stock.exchange or '').upper()
    if exchange:
        return exchange == 'NSE'
    return (stock.symbol or '').upper().endswith('.NS')


def _automation_url() -> str:
    return (current_app.config.get('AUTOMATION_URL') or '').rstrip('/')

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
                'last_updated': stock.last_updated.isoformat() + 'Z',
                'current_price': stock.current_price
            }), 429
    
    # Check global rate limit for this symbol
    symbol_key = symbol.upper()
    if symbol_key in last_update_times:
        time_since_last = time.time() - last_update_times[symbol_key]
        if time_since_last < COOLDOWN_SECONDS:
            return jsonify({
                'error': f'Please wait {int(COOLDOWN_SECONDS - time_since_last)} seconds before updating this stock again.',
                'last_updated': stock.last_updated.isoformat() + 'Z' if stock.last_updated else None,
                'current_price': stock.current_price
            }), 429
    
    try:
        current_price = fetch_current_price(symbol)
                   
        # If we got a price, update the database
        if current_price:
            stock.current_price = float(current_price)
            stock.last_updated = datetime.utcnow()

            # Also save currency if not already set
            if not stock.currency:
                try:
                    info = yf.Ticker(symbol).fast_info
                    fetched_currency = getattr(info, 'currency', None)
                    if fetched_currency:
                        stock.currency = fetched_currency.upper()
                except Exception:
                    pass

            db.session.commit()
            
            # Update cooldown tracker
            last_update_times[symbol_key] = time.time()
            
            return jsonify({
                'symbol': stock.symbol,
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() + 'Z'
            })
        else:
            return jsonify({
                'error': f'Could not fetch current price for {symbol}. The stock symbol may be invalid or temporarily unavailable.',
                'hint': 'Verify the symbol is correct for NSE stocks (e.g., RELIANCE.NS)',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() + 'Z' if stock.last_updated else None
            }), 404
            
    except Exception as e:
        error_msg = str(e)
        
        # Check for rate limiting
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                'error': 'Yahoo Finance rate limit reached. Please wait a few minutes before trying again.',
                'hint': 'Try refreshing individual stocks with longer intervals between requests.',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() + 'Z' if stock.last_updated else None
            }), 429
        elif 'HTTPError' in error_msg or 'Connection' in error_msg or 'Timeout' in error_msg:
            return jsonify({
                'error': 'Unable to connect to Yahoo Finance. Please check your internet connection and try again.',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() + 'Z' if stock.last_updated else None
            }), 503
        else:
            return jsonify({
                'error': f'Failed to fetch stock price: {error_msg}',
                'current_price': stock.current_price,
                'last_updated': stock.last_updated.isoformat() + 'Z' if stock.last_updated else None
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


@bp.route('/bulk', methods=['POST'])
def bulk_update_prices():
    """Update prices in bulk from an external source (e.g. NSE bhavcopy).

    This endpoint does NOT call Yahoo Finance - it simply applies the prices
    supplied by the caller. Only INR-denominated stocks are updated so that USD
    tickers (which may share a symbol with an Indian listing) are never touched.

    Request body:
        {
          "source": "nse-bhavcopy",
          "date": "2026-10-10",
          "prices": [
            {"symbol": "RELIANCE", "price": 2450.5},
            {"symbol": "TCS.NS",   "price": 3567.2}
          ]
        }
    """
    data = request.get_json(silent=True) or {}
    prices = data.get('prices')

    if not isinstance(prices, list) or not prices:
        return jsonify({'error': "'prices' must be a non-empty list"}), 400

    source = (data.get('source') or 'unknown').strip().lower()
    report_date = data.get('date')

    # base symbol -> [Stock, ...] (suffix-agnostic: RELIANCE / RELIANCE.NS)
    lookup = {}
    for stock in Stock.query.all():
        lookup.setdefault(_base_symbol(stock.symbol), []).append(stock)

    # Collapse duplicate rows from the source (last one wins)
    incoming = {}
    malformed = []
    for item in prices:
        if not isinstance(item, dict):
            malformed.append(str(item))
            continue
        symbol = item.get('symbol')
        price = item.get('price')
        if symbol is None or price is None:
            malformed.append(str(item))
            continue
        base = _base_symbol(str(symbol))
        if not base:
            malformed.append(str(symbol))
            continue
        incoming[base] = (symbol, price)

    updated, skipped, unmatched = [], [], []

    for base, (raw_symbol, raw_price) in incoming.items():
        try:
            price = round(float(raw_price), 2)
        except (TypeError, ValueError):
            skipped.append({'symbol': raw_symbol, 'reason': 'invalid-price'})
            continue

        candidates = lookup.get(base)
        if not candidates:
            unmatched.append(raw_symbol)
            continue

        for stock in candidates:
            if not _is_inr_stock(stock):
                skipped.append({'symbol': stock.symbol, 'reason': 'non-INR'})
                continue
            if source == 'nse-bhavcopy' and not _is_nse_stock(stock):
                skipped.append({'symbol': stock.symbol, 'reason': 'exchange-mismatch'})
                continue
            stock.current_price = price
            stock.last_updated = datetime.utcnow()
            updated.append(stock.symbol)

    db.session.commit()

    return jsonify({
        'source': source,
        'date': report_date,
        'received': len(prices),
        'updated': updated,
        'skipped': skipped,
        'unmatched': unmatched,
        'malformed': malformed,
        'updated_count': len(updated),
        'skipped_count': len(skipped),
        'unmatched_count': len(unmatched),
    }), 200


@bp.route('/sync-bhavcopy', methods=['POST'])
def trigger_bhavcopy_sync():
    """Proxy a manual NSE bhavcopy sync request to the automation service.

    Keeps the browser talking only to the backend; the automation container is
    never exposed directly. Returns the automation service response as-is.
    """
    base = _automation_url()
    if not base:
        return jsonify({'error': 'Automation service is not configured'}), 503

    payload = request.get_json(silent=True) or {}

    try:
        resp = requests.post(f'{base}/jobs/bhavcopy/run', json=payload, timeout=15)
    except requests.RequestException as exc:
        return jsonify({
            'error': 'Automation service unavailable. Is it running?',
            'detail': str(exc),
            'hint': 'Stage 1: start it with "python -m automation.app" (port 8080).',
        }), 503

    return (resp.text, resp.status_code,
            {'Content-Type': resp.headers.get('Content-Type', 'application/json')})


@bp.route('/sync-bhavcopy/status', methods=['GET'])
def bhavcopy_sync_status():
    """Proxy the NSE bhavcopy sync job status from the automation service."""
    base = _automation_url()
    if not base:
        return jsonify({'error': 'Automation service is not configured'}), 503

    try:
        resp = requests.get(f'{base}/jobs/bhavcopy/status', timeout=15)
    except requests.RequestException as exc:
        return jsonify({
            'error': 'Automation service unavailable. Is it running?',
            'detail': str(exc),
        }), 503

    return (resp.text, resp.status_code,
            {'Content-Type': resp.headers.get('Content-Type', 'application/json')})
