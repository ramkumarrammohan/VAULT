"""
Mutual fund holdings engine.

Computes current mutual fund units (and cost basis) from the mutual fund
transaction history using FIFO lot tracking. Mirrors the equity holdings engine
(backend/api/portfolio.py) but simplified to the BUY / SELL / TRANSFER model:

  BUY       - append a lot of [units, nav] (lumpsum or SIP purchase)
  SELL      - consume units FIFO (redemption)
  TRANSFER  - move units between accounts preserving cost basis

Output dicts use the SAME shape as equity holdings plus fund metadata and
asset_class='MUTUAL_FUND', so the frontend can merge them into the INR
portfolio on the dashboard.
"""
from collections import deque
from database import db
from models.account import Account
from models.mutual_fund import MutualFund
from models.mutual_fund_transaction import MutualFundTransaction


def calculate_mutual_fund_holdings():
    """Calculate current mutual fund holdings from transaction history (FIFO)."""
    transactions = (MutualFundTransaction.query
                    .order_by(MutualFundTransaction.transaction_date, MutualFundTransaction.id)
                    .all())

    if not transactions:
        return []

    lots_dict = {}  # (account_id, fund_id) -> deque of [units, nav]
    meta_dict = {}  # (account_id, fund_id) -> meta info

    for trans in transactions:
        key = (trans.account_id, trans.fund_id)
        if key not in lots_dict:
            lots_dict[key] = deque()
            fund = trans.fund
            meta_dict[key] = {
                'account_id': trans.account_id,
                'account_name': trans.account.name if trans.account else '',
                'fund_id': trans.fund_id,
                'fund_name': fund.name if fund else '',
                'scheme_code': fund.scheme_code if fund else None,
                'amc': fund.amc if fund else None,
                'category': fund.category if fund else None,
                'currency': fund.currency or 'INR' if fund else 'INR',
                'total_fees': 0.0,
            }
        lots = lots_dict[key]
        meta = meta_dict[key]

        if trans.transaction_type == 'BUY':
            lots.append([trans.quantity, trans.nav])
            meta['total_fees'] += trans.fees
        elif trans.transaction_type == 'SELL':
            remaining = trans.quantity
            while remaining > 0 and lots:
                oldest_units, oldest_nav = lots[0]
                if oldest_units <= remaining:
                    remaining -= oldest_units
                    lots.popleft()
                else:
                    lots[0][0] -= remaining
                    remaining = 0
            meta['total_fees'] += trans.fees
        elif trans.transaction_type == 'TRANSFER':
            dest_account_id = trans.transfer_to_account_id
            if dest_account_id:
                dest_key = (dest_account_id, trans.fund_id)
                if dest_key not in lots_dict:
                    lots_dict[dest_key] = deque()
                    dest_account = Account.query.get(dest_account_id)
                    dest_fund = trans.fund
                    meta_dict[dest_key] = {
                        'account_id': dest_account_id,
                        'account_name': dest_account.name if dest_account else '',
                        'fund_id': trans.fund_id,
                        'fund_name': dest_fund.name if dest_fund else '',
                        'scheme_code': dest_fund.scheme_code if dest_fund else None,
                        'amc': dest_fund.amc if dest_fund else None,
                        'category': dest_fund.category if dest_fund else None,
                        'currency': dest_fund.currency or 'INR' if dest_fund else 'INR',
                        'total_fees': 0.0,
                    }
                # FIFO move units, preserving cost basis (nav) in destination
                remaining = trans.quantity
                while remaining > 0 and lots:
                    oldest_units, oldest_nav = lots[0]
                    if oldest_units <= remaining:
                        lots_dict[dest_key].append([oldest_units, oldest_nav])
                        remaining -= oldest_units
                        lots.popleft()
                    else:
                        lots_dict[dest_key].append([remaining, oldest_nav])
                        lots[0][0] -= remaining
                        remaining = 0
                meta['total_fees'] += trans.fees

    # Convert remaining lots to output holdings
    holdings_list = []
    for key, lots in lots_dict.items():
        total_units = sum(lot[0] for lot in lots)
        if total_units <= 0:
            continue
        total_invested = sum(lot[0] * lot[1] for lot in lots)
        average_nav = total_invested / total_units if total_units > 0 else 0
        meta = meta_dict[key]

        current_nav = 0.0
        fund = MutualFund.query.get(meta['fund_id'])
        if fund and fund.nav is not None:
            current_nav = fund.nav
        current_value = total_units * current_nav
        gain_loss = current_value - total_invested
        gain_loss_percentage = (gain_loss / total_invested * 100) if total_invested > 0 else 0

        holdings_list.append({
            'account_id': meta['account_id'],
            'account_name': meta['account_name'],
            'fund_id': meta['fund_id'],
            'fund_name': meta['fund_name'],
            'scheme_code': meta['scheme_code'],
            'amc': meta['amc'],
            'category': meta['category'],
            'asset_class': 'MUTUAL_FUND',
            'currency': meta['currency'],
            'quantity': round(total_units, 4),  # units
            'average_price': round(average_nav, 4),  # weighted avg NAV
            'current_price': round(current_nav, 4),
            'invested_value': round(total_invested, 2),
            'current_value': round(current_value, 2),
            'total_fees': round(meta['total_fees'], 2),
            'gain_loss': round(gain_loss, 2),
            'gain_loss_percentage': round(gain_loss_percentage, 2),
        })

    # Sort by fund name for a stable, friendly default order
    holdings_list.sort(key=lambda h: h['fund_name'].lower())
    return holdings_list


def calculate_mutual_fund_summary(holdings=None):
    """Aggregate holdings into an overall INR summary plus category/AMC buckets."""
    if holdings is None:
        holdings = calculate_mutual_fund_holdings()

    if not holdings:
        return {
            'total_invested': 0,
            'total_current_value': 0,
            'total_gain_loss': 0,
            'total_gain_loss_percentage': 0,
            'holdings_count': 0,
            'by_category': [],
            'by_amc': [],
        }

    total_invested = sum(h['invested_value'] for h in holdings)
    total_current = sum(h['current_value'] for h in holdings)
    gain_loss = total_current - total_invested
    gain_loss_pct = (gain_loss / total_invested * 100) if total_invested > 0 else 0

    def bucket(key):
        groups = {}
        for h in holdings:
            label = h.get(key) or 'Uncategorized'
            if label not in groups:
                groups[label] = {'invested': 0.0, 'current': 0.0, 'units_count': 0}
            groups[label]['invested'] += h['invested_value']
            groups[label]['current'] += h['current_value']
            groups[label]['units_count'] += 1
        out = []
        for label, g in groups.items():
            gl = g['current'] - g['invested']
            out.append({
                'label': label,
                'total_invested': round(g['invested'], 2),
                'total_current_value': round(g['current'], 2),
                'total_gain_loss': round(gl, 2),
                'total_gain_loss_percentage': round((gl / g['invested'] * 100) if g['invested'] > 0 else 0, 2),
                'holdings_count': g['units_count'],
            })
        out.sort(key=lambda x: x['total_current_value'], reverse=True)
        return out

    return {
        'total_invested': round(total_invested, 2),
        'total_current_value': round(total_current, 2),
        'total_gain_loss': round(gain_loss, 2),
        'total_gain_loss_percentage': round(gain_loss_pct, 2),
        'holdings_count': len(holdings),
        'by_category': bucket('category'),
        'by_amc': bucket('amc'),
    }
