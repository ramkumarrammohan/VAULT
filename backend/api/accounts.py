from flask import Blueprint, request, jsonify
from database import db
from models.account import Account

bp = Blueprint('accounts', __name__)


@bp.route('/', methods=['GET'])
def get_accounts():
    """Get all accounts"""
    accounts = Account.query.all()
    return jsonify([account.to_dict() for account in accounts])


@bp.route('/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Get a specific account"""
    account = Account.query.get_or_404(account_id)
    return jsonify(account.to_dict())


@bp.route('/', methods=['POST'])
def create_account():
    """Create a new account"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    # Check if account already exists
    existing_account = Account.query.filter_by(name=data['name']).first()
    if existing_account:
        return jsonify({'error': 'Account already exists'}), 409
    
    account = Account(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(account)
    db.session.commit()
    
    return jsonify(account.to_dict()), 201


@bp.route('/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """Update an account"""
    account = Account.query.get_or_404(account_id)
    data = request.get_json()
    
    if 'name' in data:
        account.name = data['name']
    if 'description' in data:
        account.description = data['description']
    
    db.session.commit()
    return jsonify(account.to_dict())


@bp.route('/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an account"""
    account = Account.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Account deleted successfully'}), 200
