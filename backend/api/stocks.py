from flask import Blueprint, request, jsonify
from database import db
from models.stock import Stock
from datetime import datetime

bp = Blueprint('stocks', __name__)


@bp.route('/', methods=['GET'])
def get_stocks():
    """Get all stocks"""
    stocks = Stock.query.all()
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
