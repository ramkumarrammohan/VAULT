from flask import Blueprint, jsonify
from database import db
from models.transaction import Transaction
from models.holding import Holding
from models.account import Account
from models.stock import Stock
from models.corporate_event import CorporateEvent
from sqlalchemy import func

bp = Blueprint('portfolio', __name__)


def calculate_holdings_from_transactions():

    print("Calculating holdings from transactions and corporate events...")  # Debug log
    """
    Calculate current holdings from transaction history and corporate events using FIFO lot tracking.
    """
    from collections import deque
    from datetime import datetime

    # Fetch all transactions and corporate events, merge and sort by date and id
    transactions = Transaction.query.order_by(Transaction.transaction_date, Transaction.id).all()
    events = CorporateEvent.query.order_by(CorporateEvent.event_date, CorporateEvent.id).all()

    # Build a unified action list: (date, id, 'transaction'/'event', object)
    actions = []
    for t in transactions:
        actions.append((t.transaction_date, t.id, 'transaction', t))
    for e in events:
        # Use stock_id as account_id = None for events (will apply to all accounts holding the stock)
        actions.append((datetime.combine(e.event_date, datetime.min.time()), e.id, 'event', e))
    actions.sort()

    lots_dict = {}  # (account_id, stock_id) -> deque of [qty, price]
    meta_dict = {}  # (account_id, stock_id) -> meta info

    for action in actions:
        _, _, action_type, obj = action
        if action_type == 'transaction':
            trans = obj
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
                        remaining_sell -= oldest_qty
                        lots.popleft()
                    else:
                        lots[0][0] -= remaining_sell
                        remaining_sell = 0
                meta['total_fees'] += trans.fees
            # Ignore SPLIT/DEMERGER in transaction table (handled by events)
        elif action_type == 'event':
            event = obj
            # Apply event to all lots for the stock (across all accounts)
            affected_keys = [k for k in lots_dict if k[1] == event.stock_id]
            if event.event_type.name == 'SPLIT':
                # Adjust lots for split ratio (e.g., 2-for-1 split: ratio=2.0)
                for key in affected_keys:
                    lots = lots_dict[key]
                    if event.ratio and event.ratio > 0:
                        for lot in lots:
                            lot[0] *= event.ratio
                            lot[1] /= event.ratio
            elif event.event_type.name == 'DEMERGER':
                # For each account holding the parent stock, split cost basis and add new lots for the demerged company
                for key in affected_keys:
                    account_id, parent_stock_id = key
                    lots = lots_dict[key]
                    total_parent_shares = sum(lot[0] for lot in lots)
                    total_parent_cost = sum(lot[0] * lot[1] for lot in lots)
                    if event.ratio and event.related_stock_id and total_parent_shares > 0 and event.parent_cost_pct is not None and event.demerged_cost_pct is not None:
                        # Calculate new shares: e.g., 1 for every 10 held (ratio=0.1)
                        new_shares = total_parent_shares * event.ratio
                        # Apportion cost basis
                        parent_cost = total_parent_cost * (event.parent_cost_pct / 100.0)
                        demerged_cost = total_parent_cost * (event.demerged_cost_pct / 100.0)
                        # Adjust parent lots' cost basis proportionally
                        if total_parent_cost > 0:
                            for lot in lots:
                                orig_cost = lot[0] * lot[1]
                                if orig_cost > 0:
                                    new_cost = orig_cost * (event.parent_cost_pct / 100.0)
                                    lot[1] = new_cost / lot[0]
                        # Add new lot for demerged company
                        if new_shares > 0:
                            new_key = (account_id, event.related_stock_id)
                            if new_key not in lots_dict:
                                lots_dict[new_key] = deque()
                                stock = Stock.query.get(event.related_stock_id)
                                meta_dict[new_key] = {
                                    'account_id': account_id,
                                    'account_name': meta_dict[key]['account_name'],
                                    'stock_id': event.related_stock_id,
                                    'stock_symbol': stock.symbol if stock else '',
                                    'stock_name': stock.name if stock else '',
                                    'total_fees': meta_dict[key]['total_fees'],
                                }
                            # Correct calculation: apportioned cost divided by new shares
                            demerged_price = demerged_cost / new_shares if new_shares > 0 else 0.0
                            lots_dict[new_key].append([new_shares, demerged_price])
            elif event.event_type.name in ('MERGER', 'AMALGAMATION'):
                # Move/merge lots from old to new stock, adjust quantities and cost basis
                for key in affected_keys:
                    account_id, old_stock_id = key
                    lots = lots_dict[key]
                    total_old_shares = sum(lot[0] for lot in lots)
                    total_old_cost = sum(lot[0] * lot[1] for lot in lots)
                    if event.related_stock_id and total_old_shares > 0:
                        # Add/adjust lots for new stock FIRST, using original prices
                        new_key = (account_id, event.related_stock_id)
                        if new_key not in lots_dict:
                            lots_dict[new_key] = deque()
                            stock = Stock.query.get(event.related_stock_id)
                            meta_dict[new_key] = {
                                'account_id': account_id,
                                'account_name': meta_dict[key]['account_name'],
                                'stock_id': event.related_stock_id,
                                'stock_symbol': stock.symbol if stock else '',
                                'stock_name': stock.name if stock else '',
                                'total_fees': meta_dict[key]['total_fees'],
                            }
                        demerged_pct = event.demerged_cost_pct / 100.0 if event.demerged_cost_pct is not None else 1.0
                        parent_pct = event.parent_cost_pct / 100.0 if event.parent_cost_pct is not None else 0.0
                        # For each lot, transfer shares and cost as per ratio using original prices
                        for lot in list(lots_dict[key]):
                            qty = lot[0]
                            orig_price = lot[1]
                            qty_new = qty * event.ratio if (event.ratio and event.ratio > 0) else qty
                            lot_cost = qty * orig_price
                            transferred_cost = lot_cost * demerged_pct
                            new_price = transferred_cost / qty_new if qty_new > 0 else 0.0
                            lots_dict[new_key].append([qty_new, new_price])
                        # Extinguish old stock lots — old company ceases to exist in a merger/amalgamation
                        lots_dict[key].clear()
            # DIVIDEND and NAME_CHANGE do not affect lots (for reporting only)

    # Convert remaining lots to output holdings
    holdings_list = []
    for key, lots in lots_dict.items():
        if not lots:
            continue
        total_qty = sum(lot[0] for lot in lots)
        if total_qty <= 0:
            continue
        total_invested = sum(lot[0] * lot[1] for lot in lots)
        average_price = total_invested / total_qty if total_qty > 0 else 0
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

