from flask import Blueprint, request, jsonify
from database import db
from models.holding import Holding
from models.stock import Stock
from models.account import Account

bp = Blueprint('holdings', __name__)


@bp.route('/', methods=['GET'])
def get_holdings():
    """Get all holdings"""
    holdings = Holding.query.all()
    return jsonify([holding.to_dict() for holding in holdings])


@bp.route('/<int:holding_id>', methods=['GET'])
def get_holding(holding_id):
    """Get a specific holding"""
    holding = Holding.query.get_or_404(holding_id)
    return jsonify(holding.to_dict())


@bp.route('/', methods=['POST'])
def create_holding():
    """Create a new holding"""
    data = request.get_json()
    
    required_fields = ['account_id', 'stock_id', 'quantity', 'average_price']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'account_id, stock_id, quantity, and average_price are required'}), 400
    
    # Verify account and stock exist
    account = Account.query.get(data['account_id'])
    stock = Stock.query.get(data['stock_id'])
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404
    
    # Check if holding already exists
    existing_holding = Holding.query.filter_by(
        account_id=data['account_id'],
        stock_id=data['stock_id']
    ).first()
    
    if existing_holding:
        return jsonify({'error': 'Holding already exists for this account and stock'}), 409
    
    holding = Holding(
        account_id=data['account_id'],
        stock_id=data['stock_id'],
        quantity=data['quantity'],
        average_price=data['average_price'],
        notes=data.get('notes')
    )
    
    db.session.add(holding)
    db.session.commit()
    
    return jsonify(holding.to_dict()), 201


@bp.route('/<int:holding_id>', methods=['PUT'])
def update_holding(holding_id):
    """Update a holding"""
    holding = Holding.query.get_or_404(holding_id)
    data = request.get_json()
    
    if 'quantity' in data:
        holding.quantity = data['quantity']
    if 'average_price' in data:
        holding.average_price = data['average_price']
    if 'notes' in data:
        holding.notes = data['notes']
    
    db.session.commit()
    return jsonify(holding.to_dict())


@bp.route('/<int:holding_id>', methods=['DELETE'])
def delete_holding(holding_id):
    """Delete a holding"""
    holding = Holding.query.get_or_404(holding_id)
    db.session.delete(holding)
    db.session.commit()
    return jsonify({'message': 'Holding deleted successfully'}), 200
