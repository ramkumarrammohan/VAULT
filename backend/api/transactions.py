from flask import Blueprint, request, jsonify
from database import db
from models.transaction import Transaction
from models.account import Account
from models.stock import Stock
from datetime import datetime

bp = Blueprint('transactions', __name__)


@bp.route('/', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    # Optional filtering by account_id and stock_id
    account_id = request.args.get('account_id', type=int)
    stock_id = request.args.get('stock_id', type=int)
    
    query = Transaction.query
    if account_id:
        query = query.filter_by(account_id=account_id)
    if stock_id:
        query = query.filter_by(stock_id=stock_id)
    
    transactions = query.order_by(Transaction.transaction_date.desc()).all()
    
    return jsonify([transaction.to_dict() for transaction in transactions])


@bp.route('/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get a specific transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    return jsonify(transaction.to_dict())


@bp.route('/', methods=['POST'])
def create_transaction():
    """Create a new transaction"""
    data = request.get_json()
    
    required_fields = ['account_id', 'stock_id', 'transaction_type', 'quantity', 'price', 'transaction_date']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'account_id, stock_id, transaction_type, quantity, price, and transaction_date are required'}), 400
    
    # Validate transaction type
    if data['transaction_type'] not in ['BUY', 'SELL']:
        return jsonify({'error': 'transaction_type must be either BUY or SELL'}), 400
    
    # Verify account and stock exist
    account = Account.query.get(data['account_id'])
    stock = Stock.query.get(data['stock_id'])
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404
    
    # Parse transaction date
    try:
        if isinstance(data['transaction_date'], str):
            transaction_date = datetime.fromisoformat(data['transaction_date'].replace('Z', '+00:00'))
        else:
            transaction_date = data['transaction_date']
    except (ValueError, AttributeError):
        return jsonify({'error': 'Invalid transaction_date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400
    
    transaction = Transaction(
        account_id=data['account_id'],
        stock_id=data['stock_id'],
        transaction_type=data['transaction_type'],
        quantity=data['quantity'],
        price=data['price'],
        transaction_date=transaction_date,
        fees=data.get('fees', 0),
        notes=data.get('notes')
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(transaction.to_dict()), 201


@bp.route('/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Update a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    data = request.get_json()
    
    # Note: Updating transactions is tricky as it affects holdings
    # For MVP, allow updating only notes and fees
    if 'notes' in data:
        transaction.notes = data['notes']
    if 'fees' in data:
        transaction.fees = data['fees']
    
    db.session.commit()
    return jsonify(transaction.to_dict())


@bp.route('/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({'message': 'Transaction deleted successfully'}), 200

