from flask import Blueprint, request, jsonify
from database import db
from models.stock import Stock
from datetime import datetime

bp = Blueprint('stocks', __name__)

# Maps known exchange codes to their base currency
_EXCHANGE_CURRENCY = {
    'NSE': 'INR', 'BSE': 'INR',
    'NYSE': 'USD', 'NASDAQ': 'USD', 'NMS': 'USD', 'NYQ': 'USD',
    'NGM': 'USD', 'NCM': 'USD', 'ASE': 'USD',
}


def _infer_currency(symbol: str, exchange: str | None) -> str | None:
    """Infer currency from exchange code or symbol suffix."""
    if exchange and exchange.upper() in _EXCHANGE_CURRENCY:
        return _EXCHANGE_CURRENCY[exchange.upper()]
    sym = (symbol or '').upper()
    if sym.endswith('.NS') or sym.endswith('.BO'):
        return 'INR'
    return None


@bp.route('/', methods=['GET'])
def get_stocks():
    """Get all stocks"""
    stocks = Stock.query.order_by(Stock.name.asc()).all()
    return jsonify([stock.to_dict() for stock in stocks])


@bp.route('/<int:stock_id>', methods=['GET'])
def get_stock(stock_id):
    """Get a specific stock"""
    stock = Stock.query.get_or_404(stock_id)
    return jsonify(stock.to_dict())


@bp.route('/', methods=['POST'])
def create_stock():
    """Create a new stock"""
    data = request.get_json()
    
    if not data or 'symbol' not in data or 'name' not in data:
        return jsonify({'error': 'Symbol and name are required'}), 400
    
    # Check if stock already exists
    existing_stock = Stock.query.filter_by(symbol=data['symbol'].upper()).first()
    if existing_stock:
        return jsonify({'error': 'Stock already exists'}), 409
    
    stock = Stock(
        symbol=data['symbol'].upper(),
        name=data['name'],
        exchange=data.get('exchange'),
        sector=data.get('sector'),
        currency=data.get('currency') or _infer_currency(data['symbol'], data.get('exchange')),
        current_price=data.get('current_price'),
        last_updated=datetime.utcnow() if data.get('current_price') else None
    )
    
    db.session.add(stock)
    db.session.commit()
    
    return jsonify(stock.to_dict()), 201


@bp.route('/<int:stock_id>', methods=['PUT'])
def update_stock(stock_id):
    """Update a stock"""
    stock = Stock.query.get_or_404(stock_id)
    data = request.get_json()
    
    if 'symbol' in data:
        stock.symbol = data['symbol'].upper()
    if 'name' in data:
        stock.name = data['name']
    if 'exchange' in data:
        stock.exchange = data['exchange']
    if 'sector' in data:
        stock.sector = data['sector']
    if 'currency' in data:
        # Explicit override takes precedence; empty string clears back to auto-detect
        stock.currency = data['currency'] or _infer_currency(stock.symbol, stock.exchange)
    elif 'exchange' in data and not stock.currency:
        # Re-infer when exchange changes and currency wasn't set before
        stock.currency = _infer_currency(stock.symbol, data['exchange'])
    if 'current_price' in data:
        stock.current_price = data['current_price']
        stock.last_updated = datetime.utcnow()
    
    db.session.commit()
    return jsonify(stock.to_dict())


@bp.route('/<int:stock_id>', methods=['DELETE'])
def delete_stock(stock_id):
    """Delete a stock"""
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    return jsonify({'message': 'Stock deleted successfully'}), 200
