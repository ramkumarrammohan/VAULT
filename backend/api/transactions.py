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


@bp.route('/bulk', methods=['POST'])
def create_bulk_transactions():
    """Create multiple transactions at once from CSV data"""
    try:
        data = request.get_json()
        print(f"Received bulk request data: {data}")  # Debug log
        
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({'error': 'No data provided'}), 400
            
        if 'transactions' not in data:
            print(f"ERROR: 'transactions' key not found. Keys: {data.keys()}")
            return jsonify({'error': 'transactions array is required'}), 400
        
        transactions_data = data['transactions']
        if not isinstance(transactions_data, list):
            print(f"ERROR: transactions is not a list. Type: {type(transactions_data)}")
            return jsonify({'error': 'transactions must be an array'}), 400
            
        if len(transactions_data) == 0:
            print("ERROR: transactions array is empty")
            return jsonify({'error': 'transactions array cannot be empty'}), 400
        
        print(f"Processing {len(transactions_data)} transactions")  # Debug log
        
        created_transactions = []
        errors = []
    except Exception as e:
        print(f"ERROR parsing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to parse request: {str(e)}'}), 400
    
    for idx, trans_data in enumerate(transactions_data):
        try:
            print(f"Processing transaction {idx + 1}: {trans_data}")  # Debug log
            
            # Validate required fields
            required_fields = ['account_id', 'stock_id', 'transaction_type', 'quantity', 'price', 'transaction_date']
            missing_fields = [field for field in required_fields if field not in trans_data]
            if missing_fields:
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                print(f"Row {idx + 1} error: {error_msg}")  # Debug log
                errors.append({
                    'row': idx + 1,
                    'error': error_msg
                })
                continue
            
            # Validate transaction type
            if trans_data['transaction_type'] not in ['BUY', 'SELL']:
                errors.append({
                    'row': idx + 1,
                    'error': 'transaction_type must be either BUY or SELL'
                })
                continue
            
            # Verify account and stock exist
            account = Account.query.get(trans_data['account_id'])
            stock = Stock.query.get(trans_data['stock_id'])
            
            if not account:
                errors.append({
                    'row': idx + 1,
                    'error': f'Account with id {trans_data["account_id"]} not found'
                })
                continue
            if not stock:
                errors.append({
                    'row': idx + 1,
                    'error': f'Stock with id {trans_data["stock_id"]} not found'
                })
                continue
            
            # Parse transaction date - handle multiple date formats
            try:
                if isinstance(trans_data['transaction_date'], str):
                    date_str = trans_data['transaction_date'].strip()
                    transaction_date = None
                    
                    # Try multiple date formats
                    date_formats = [
                        '%d-%m-%Y',          # DD-MM-YYYY
                        '%Y-%m-%d',          # YYYY-MM-DD
                        '%m/%d/%Y',          # MM/DD/YYYY
                        '%d/%m/%Y',          # DD/MM/YYYY
                        '%Y-%m-%dT%H:%M:%S', # ISO format with time
                        '%Y-%m-%d %H:%M:%S', # YYYY-MM-DD HH:MM:SS
                    ]
                    
                    for fmt in date_formats:
                        try:
                            transaction_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if transaction_date is None:
                        # Last attempt with fromisoformat
                        try:
                            transaction_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if transaction_date is None:
                        raise ValueError(f"Unable to parse date: {date_str}")
                else:
                    transaction_date = trans_data['transaction_date']
            except (ValueError, AttributeError) as e:
                errors.append({
                    'row': idx + 1,
                    'error': f'Invalid transaction_date format: {str(e)}'
                })
                print(f"Row {idx + 1} date error: {str(e)}")
                continue
            
            transaction = Transaction(
                account_id=trans_data['account_id'],
                stock_id=trans_data['stock_id'],
                transaction_type=trans_data['transaction_type'],
                quantity=trans_data['quantity'],
                price=trans_data['price'],
                transaction_date=transaction_date,
                fees=trans_data.get('fees', 0),
                notes=trans_data.get('notes')
            )
            
            db.session.add(transaction)
            created_transactions.append(transaction)
            
        except Exception as e:
            errors.append({
                'row': idx + 1,
                'error': str(e)
            })
    
    # Only commit if there are successful transactions
    if created_transactions:
        db.session.commit()
    
    return jsonify({
        'success_count': len(created_transactions),
        'error_count': len(errors),
        'errors': errors,
        'created': [t.to_dict() for t in created_transactions]
    }), 201 if created_transactions else 400

