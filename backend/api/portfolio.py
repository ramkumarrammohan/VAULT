from flask import Blueprint, jsonify
from database import db
from models.transaction import Transaction
from models.holding import Holding
from models.account import Account
from models.stock import Stock
from sqlalchemy import func

bp = Blueprint('portfolio', __name__)


def calculate_holdings_from_transactions():
    print("Calculating holdings from transactions...")  # Debug log
    """Calculate current holdings from transaction history using FIFO lot tracking.

    Zerodha-aligned FIFO logic:
      BUY      → append a new lot (quantity, price) to the back of the queue
      SELL     → consume lots from the front (oldest first); partial lots allowed
      SPLIT /
      BONUS    → for each existing lot: qty *= (old+new)/old, price *= old/(old+new)
                 (i.e. split the transaction quantity across lots proportionally,
                  keeping total invested value per lot unchanged)
      DEMERGER → append a zero-cost lot for the received shares

    After processing, average_price = WAC of the remaining (oldest) lots.
    """
    from collections import deque

    # Process transactions chronologically; use id to break same-day ties
    transactions = Transaction.query.order_by(
        Transaction.transaction_date, Transaction.id
    ).all()

    # lots_dict: (account_id, stock_id) → deque of [qty, price] pairs (oldest first)
    lots_dict = {}
    meta_dict = {}   # stores account/stock names and total_fees

    for trans in transactions:
        key = (trans.account_id, trans.stock_id)

        if key not in lots_dict:
            lots_dict[key] = deque()
            meta_dict[key] = {
                'account_id': trans.account_id,
                'account_name': trans.account.name,
                'stock_id': trans.stock_id,
                'stock_symbol': trans.stock.symbol,
                'stock_name': trans.stock.name,
                'total_fees': 0.0,
            }

        lots = lots_dict[key]
        meta = meta_dict[key]

        if trans.transaction_type == 'BUY':
            lots.append([trans.quantity, trans.price])
            meta['total_fees'] += trans.fees

        elif trans.transaction_type == 'SELL':
            remaining_sell = trans.quantity
            while remaining_sell > 0 and lots:
                oldest_qty, oldest_price = lots[0]
                if oldest_qty <= remaining_sell:
                    # Entire oldest lot is consumed
                    remaining_sell -= oldest_qty
                    lots.popleft()
                else:
                    # Partial consumption of oldest lot
                    lots[0][0] -= remaining_sell
                    remaining_sell = 0
            meta['total_fees'] += trans.fees

        elif trans.transaction_type == 'SPLIT':
            # trans.quantity = total bonus/split shares received for this holding.
            # Distribute proportionally across existing lots so that each lot's
            # invested value is unchanged and its per-share cost drops accordingly.
            total_existing = sum(lot[0] for lot in lots)
            if total_existing > 0:
                ratio = (total_existing + trans.quantity) / total_existing
                for lot in lots:
                    lot[1] = lot[1] / ratio          # price per share decreases
                    lot[0] = lot[0] * ratio           # qty increases

        elif trans.transaction_type == 'DEMERGER':
            # Received shares from a corporate action; zero acquisition cost.
            lots.append([trans.quantity, 0.0])

    # Convert remaining lots to output holdings
    holdings_list = []
    for key, lots in lots_dict.items():
        if not lots:
            continue

        total_qty = sum(lot[0] for lot in lots)
        if total_qty <= 0:
            continue

        # Average price = WAC of remaining FIFO lots (matches what Zerodha shows)
        total_invested = sum(lot[0] * lot[1] for lot in lots)
        average_price = total_invested / total_qty

        meta = meta_dict[key]
        stock = Stock.query.get(meta['stock_id'])
        current_price = stock.current_price or 0
        current_value = total_qty * current_price
        gain_loss = current_value - total_invested
        gain_loss_percentage = (gain_loss / total_invested * 100) if total_invested > 0 else 0

        holdings_list.append({
            'account_id': meta['account_id'],
            'account_name': meta['account_name'],
            'stock_id': meta['stock_id'],
            'stock_symbol': meta['stock_symbol'],
            'stock_name': meta['stock_name'],
            'quantity': round(total_qty, 4),
            'average_price': round(average_price, 2),
            'current_price': round(current_price, 2),
            'invested_value': round(total_invested, 2),
            'current_value': round(current_value, 2),
            'total_fees': round(meta['total_fees'], 2),
            'gain_loss': round(gain_loss, 2),
            'gain_loss_percentage': round(gain_loss_percentage, 2),
        })

    return holdings_list


@bp.route('/holdings', methods=['GET'])
def get_holdings():
    """Get current holdings calculated from transactions"""
    print("API call: GET /portfolio/holdings")  # Debug log
    holdings = calculate_holdings_from_transactions()
    return jsonify(holdings)


@bp.route('/summary', methods=['GET'])
def get_portfolio_summary():
    """Get overall portfolio summary"""
    holdings = calculate_holdings_from_transactions()
    
    if not holdings:
        return jsonify({
            'total_invested': 0,
            'total_current_value': 0,
            'total_gain_loss': 0,
            'total_gain_loss_percentage': 0,
            'holdings_count': 0,
            'accounts_count': 0
        })
    
    total_invested = sum(h['invested_value'] for h in holdings)
    total_current_value = sum(h['current_value'] for h in holdings)
    total_gain_loss = total_current_value - total_invested
    total_gain_loss_percentage = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    accounts_count = len(set(h['account_id'] for h in holdings))
    
    return jsonify({
        'total_invested': round(total_invested, 2),
        'total_current_value': round(total_current_value, 2),
        'total_gain_loss': round(total_gain_loss, 2),
        'total_gain_loss_percentage': round(total_gain_loss_percentage, 2),
        'holdings_count': len(holdings),
        'accounts_count': accounts_count
    })


@bp.route('/by-account', methods=['GET'])
def get_portfolio_by_account():
    """Get portfolio summary grouped by account"""
    holdings = calculate_holdings_from_transactions()
    
    account_dict = {}
    
    for holding in holdings:
        account_id = holding['account_id']
        
        if account_id not in account_dict:
            account_dict[account_id] = {
                'account_id': account_id,
                'account_name': holding['account_name'],
                'total_invested': 0,
                'total_current_value': 0,
                'holdings_count': 0
            }
        
        account_dict[account_id]['total_invested'] += holding['invested_value']
        account_dict[account_id]['total_current_value'] += holding['current_value']
        account_dict[account_id]['holdings_count'] += 1
    
    account_summaries = []
    for account_data in account_dict.values():
        total_gain_loss = account_data['total_current_value'] - account_data['total_invested']
        total_gain_loss_percentage = (total_gain_loss / account_data['total_invested'] * 100) if account_data['total_invested'] > 0 else 0
        
        account_summaries.append({
            'account_id': account_data['account_id'],
            'account_name': account_data['account_name'],
            'total_invested': round(account_data['total_invested'], 2),
            'total_current_value': round(account_data['total_current_value'], 2),
            'total_gain_loss': round(total_gain_loss, 2),
            'total_gain_loss_percentage': round(total_gain_loss_percentage, 2),
            'holdings_count': account_data['holdings_count']
        })
    
    return jsonify(account_summaries)


@bp.route('/top-performers', methods=['GET'])
def get_top_performers():
    """Get top performing holdings by gain/loss percentage"""
    holdings = calculate_holdings_from_transactions()
    
    # Sort by gain/loss percentage
    sorted_holdings = sorted(holdings, key=lambda x: x['gain_loss_percentage'], reverse=True)
    
    return jsonify({
        'top_gainers': sorted_holdings[:5],
        'top_losers': sorted_holdings[-5:] if len(sorted_holdings) > 5 else []
    })

