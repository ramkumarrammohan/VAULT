from flask import Blueprint, request, jsonify
from database import db
from models.account import Account
from models.mutual_fund import MutualFund
from models.mutual_fund_transaction import MutualFundTransaction
from datetime import datetime, time
import time as time_module
import mf_nav
from mf_holdings import calculate_mutual_fund_holdings, calculate_mutual_fund_summary

bp = Blueprint('mutual_funds', __name__)

TRANSACTION_TYPES = ['BUY', 'SELL', 'TRANSFER']
COOLDOWN_SECONDS = 60  # Minimum seconds between NAV refreshes for the same fund

# Simple per-process tracker to also guard repeated refresh-all calls
_last_bulk_nav_update = {}


def _parse_datetime(value):
    """Parse a transaction date from many common formats. Raises ValueError."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError('transaction_date must be a string or datetime')
    text = value.strip()
    formats = [
        '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
        '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f'Invalid date format: {text}')


def _parse_nav_date(value):
    """Parse a NAV date (date only is fine) -> datetime at midnight UTC."""
    try:
        dt = _parse_datetime(value)
    except ValueError:
        # Try day-first with time pieces removed
        try:
            dt = datetime.strptime(str(value).strip(), '%d-%m-%Y')
        except ValueError:
            raise ValueError(f'Invalid nav_date: {value}')
    return datetime.combine(dt.date(), time.min)


def _resolve_account(data):
    if data.get('account_id'):
        return Account.query.get(int(data['account_id']))
    name = (data.get('account_name') or '').strip()
    if name:
        return Account.query.filter(db.func.lower(Account.name) == name.lower()).first()
    return None


def _resolve_destination_account(data):
    if data.get('transfer_to_account_id'):
        return Account.query.get(int(data['transfer_to_account_id']))
    name = (data.get('transfer_to_account_name') or '').strip()
    if name:
        return Account.query.filter(db.func.lower(Account.name) == name.lower()).first()
    return None


def _resolve_fund(data):
    if data.get('fund_id'):
        return MutualFund.query.get(int(data['fund_id']))
    code = (data.get('scheme_code') or '').strip()
    if code:
        return MutualFund.query.filter_by(scheme_code=code.upper()).first()
    name = (data.get('fund_name') or '').strip()
    if name:
        return MutualFund.query.filter(db.func.lower(MutualFund.name) == name.lower()).first()
    return None


def _derive_units_nav(fund, quantity, nav, amount, transaction_date, is_transfer=False):
    """Return (quantity_units, nav_per_unit) resolved from the provided inputs.

    Accepts any two of quantity/amount/nav, or auto-fetches the NAV on the
    transaction date when only the amount is supplied (and the fund has an
    AMFI scheme_code). For TRANSFER transactions only `quantity` (units) is
    required; nav defaults to 0 since cost basis is preserved from the source
    lots. Raises ValueError if it cannot be resolved.
    """
    if is_transfer:
        if quantity is None:
            raise ValueError('quantity (units) is required for TRANSFER transactions')
        return round(float(quantity), 4), 0.0

    if quantity is None and nav is None and amount is None:
        raise ValueError('At least one of quantity (units), nav, or amount is required')

    if nav is None and amount is not None and quantity is not None and amount > 0:
        nav = amount / quantity
    elif quantity is None and amount is not None and nav is not None and nav > 0:
        quantity = amount / nav
    elif quantity is None and nav is None and amount is not None:
        # Auto-fetch historical NAV on transaction date to compute units
        if not (fund and fund.scheme_code):
            raise ValueError('Cannot auto-compute units: no AMFI scheme_code for this fund. '
                             'Provide quantity (units) or NAV.')
        fetched = mf_nav.fetch_nav_on(fund.scheme_code, transaction_date, fallback='previous')
        if not fetched:
            raise ValueError('No NAV available near the transaction date to compute units.')
        nav = fetched[0]
        quantity = amount / nav

    if nav is None or nav <= 0:
        raise ValueError('NAV must be a positive number (provide amount or a valid NAV).')
    if quantity is None:
        raise ValueError('Unable to determine quantity (units). Provide amount/units or a valid NAV.')
    return round(float(quantity), 4), round(float(nav), 4)


# --------------------------------------------------------------------------
# Scheme discovery / lookup (mfapi.in / AMFI)
# --------------------------------------------------------------------------

@bp.route('/search', methods=['GET'])
def search_schemes():
    """Search AMFI schemes by name keyword."""
    query = request.args.get('q', '')
    if not query.strip():
        return jsonify({'error': 'Search query q is required'}), 400
    try:
        results = mf_nav.search_schemes(query)
    except mf_nav.NavError as e:
        return jsonify({'error': e.message, 'hint': e.hint}), e.status_code
    return jsonify({'results': results})


@bp.route('/scheme/<string:scheme_code>', methods=['GET'])
def get_scheme_info(scheme_code):
    """Fetch scheme metadata + latest NAV from the provider (form auto-fill)."""
    try:
        data = mf_nav.fetch_scheme_data(scheme_code)
    except mf_nav.NavError as e:
        return jsonify({'error': e.message, 'hint': e.hint}), e.status_code

    meta = data['meta']
    latest = data['history'][-1]
    name = meta.get('scheme_name') or ''
    lower = name.lower()

    plan = None
    option = None
    if 'direct' in lower:
        plan = 'DIRECT'
    elif 'regular' in lower:
        plan = 'REGULAR'
    if 'growth' in lower:
        option = 'GROWTH'
    elif 'idcw' in lower or 'dividend' in lower:
        option = 'IDCW'

    return jsonify({
        'scheme_code': scheme_code,
        'scheme_name': name,
        'amc': meta.get('fund_house'),
        'category': meta.get('scheme_category'),
        'scheme_type': meta.get('scheme_type'),
        'plan': plan,
        'option': option,
        'nav': latest['nav'],
        'nav_date': latest['date'],
    })


# --------------------------------------------------------------------------
# Fund CRUD
# --------------------------------------------------------------------------

@bp.route('/', methods=['GET'])
def get_mutual_funds():
    """Get all mutual funds ordered by name."""
    funds = MutualFund.query.order_by(MutualFund.name.asc()).all()
    return jsonify([fund.to_dict() for fund in funds])


@bp.route('/overview', methods=['GET'])
def get_mutual_funds_overview():
    """Get all funds enriched with computed aggregate holdings across accounts."""
    funds = MutualFund.query.order_by(MutualFund.name.asc()).all()
    holdings = calculate_mutual_fund_holdings()

    totals_by_fund = {}
    for h in holdings:
        fid = h['fund_id']
        if fid not in totals_by_fund:
            totals_by_fund[fid] = {
                'quantity': 0.0, 'invested_value': 0.0, 'current_value': 0.0,
                'gain_loss': 0.0, 'accounts_count': 0,
            }
        t = totals_by_fund[fid]
        t['quantity'] += h['quantity']
        t['invested_value'] += h['invested_value']
        t['current_value'] += h['current_value']
        t['gain_loss'] += h['gain_loss']

    overview = []
    for fund in funds:
        item = fund.to_dict()
        t = totals_by_fund.get(fund.id)
        if t:
            item.update({
                'total_units': round(t['quantity'], 4),
                'total_invested': round(t['invested_value'], 2),
                'total_current_value': round(t['current_value'], 2),
                'total_gain_loss': round(t['gain_loss'], 2),
                'total_gain_loss_percentage': round(
                    (t['gain_loss'] / t['invested_value'] * 100) if t['invested_value'] > 0 else 0, 2),
            })
        else:
            item.update({
                'total_units': 0, 'total_invested': 0,
                'total_current_value': 0, 'total_gain_loss': 0,
                'total_gain_loss_percentage': 0,
            })
        overview.append(item)
    return jsonify(overview)


@bp.route('/<int:fund_id>', methods=['GET'])
def get_mutual_fund(fund_id):
    """Get a specific mutual fund."""
    fund = MutualFund.query.get_or_404(fund_id)
    return jsonify(fund.to_dict())


@bp.route('/', methods=['POST'])
def create_mutual_fund():
    """Create a new mutual fund."""
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Fund name is required'}), 400

    scheme_code = (data.get('scheme_code') or '').strip().upper() or None
    if scheme_code:
        existing = MutualFund.query.filter_by(scheme_code=scheme_code).first()
        if existing:
            return jsonify({'error': f'A fund with scheme code {scheme_code} already exists'}), 409

    nav = data.get('nav')
    nav_date = None
    if data.get('nav_date'):
        try:
            nav_date = _parse_nav_date(data['nav_date'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    fund = MutualFund(
        scheme_code=scheme_code,
        name=data['name'].strip(),
        amc=data.get('amc'),
        category=data.get('category'),
        plan=(data.get('plan') or '').upper() or None,
        option=(data.get('option') or '').upper() or None,
        isin=data.get('isin'),
        folio=data.get('folio'),
        currency=(data.get('currency') or 'INR').upper(),
        nav=float(nav) if nav is not None else None,
        nav_date=nav_date,
        last_updated=datetime.utcnow() if nav is not None else None,
    )
    db.session.add(fund)
    db.session.commit()
    return jsonify(fund.to_dict()), 201


@bp.route('/<int:fund_id>', methods=['PUT'])
def update_mutual_fund(fund_id):
    """Update a mutual fund."""
    fund = MutualFund.query.get_or_404(fund_id)
    data = request.get_json()

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'error': 'Fund name cannot be empty'}), 400
        fund.name = data['name'].strip()
    if 'scheme_code' in data:
        code = (data['scheme_code'] or '').strip().upper() or None
        if code:
            existing = MutualFund.query.filter(MutualFund.scheme_code == code,
                                               MutualFund.id != fund.id).first()
            if existing:
                return jsonify({'error': f'A fund with scheme code {code} already exists'}), 409
        fund.scheme_code = code
    for field in ('amc', 'category', 'plan', 'option', 'isin', 'folio'):
        if field in data:
            setattr(fund, field, (data.get(field) or '').strip() or None)
    if 'currency' in data:
        fund.currency = (data['currency'] or 'INR').upper()
    if 'nav' in data:
        fund.nav = float(data['nav']) if data['nav'] is not None else None
        fund.last_updated = datetime.utcnow() if fund.nav is not None else fund.last_updated
    if 'nav_date' in data and data['nav_date']:
        try:
            fund.nav_date = _parse_nav_date(data['nav_date'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    db.session.commit()
    return jsonify(fund.to_dict())


@bp.route('/<int:fund_id>', methods=['DELETE'])
def delete_mutual_fund(fund_id):
    """Delete a mutual fund (and its transactions)."""
    fund = MutualFund.query.get_or_404(fund_id)
    db.session.delete(fund)
    db.session.commit()
    return jsonify({'message': 'Mutual fund deleted successfully'}), 200


# --------------------------------------------------------------------------
# Holdings / summary
# --------------------------------------------------------------------------

@bp.route('/holdings', methods=['GET'])
def get_holdings():
    """Get current mutual fund holdings computed from transactions (FIFO)."""
    holdings = calculate_mutual_fund_holdings()
    return jsonify(holdings)


@bp.route('/summary', methods=['GET'])
def get_summary():
    """Get mutual fund portfolio summary (INR) with category/AMC breakdowns."""
    return jsonify(calculate_mutual_fund_summary())


# --------------------------------------------------------------------------
# Fund transactions
# --------------------------------------------------------------------------

@bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get mutual fund transactions, optionally filtered by account/fund."""
    account_id = request.args.get('account_id', type=int)
    fund_id = request.args.get('fund_id', type=int)

    query = MutualFundTransaction.query
    if account_id:
        query = query.filter_by(account_id=account_id)
    if fund_id:
        query = query.filter_by(fund_id=fund_id)

    transactions = query.order_by(MutualFundTransaction.transaction_date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])


@bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Create a single mutual fund transaction."""
    data = request.get_json()
    required = ['account_id', 'fund_id', 'transaction_type', 'transaction_date']
    if not data or not all(field in data for field in required):
        return jsonify({'error': 'account_id, fund_id, transaction_type, and transaction_date are required'}), 400
    if data['transaction_type'] not in TRANSACTION_TYPES:
        return jsonify({'error': 'transaction_type must be BUY, SELL, or TRANSFER'}), 400

    account = Account.query.get(data['account_id'])
    fund = MutualFund.query.get(data['fund_id'])
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    if not fund:
        return jsonify({'error': 'Mutual fund not found'}), 404

    if data['transaction_type'] == 'TRANSFER':
        if not data.get('transfer_to_account_id'):
            return jsonify({'error': 'transfer_to_account_id is required for TRANSFER transactions'}), 400
        if int(data['transfer_to_account_id']) == int(data['account_id']):
            return jsonify({'error': 'transfer_to_account_id must differ from account_id'}), 400

    try:
        transaction_date = _parse_datetime(data['transaction_date'])
    except ValueError as e:
        return jsonify({'error': f'Invalid transaction_date: {e}'}), 400

    try:
        quantity, nav = _derive_units_nav(
            fund, data.get('quantity'), data.get('nav'), data.get('amount'), transaction_date,
            is_transfer=(data['transaction_type'] == 'TRANSFER'))
    except (ValueError, mf_nav.NavError) as e:
        msg = e.message if isinstance(e, mf_nav.NavError) else str(e)
        return jsonify({'error': msg}), 400

    transaction = MutualFundTransaction(
        account_id=account.id,
        fund_id=fund.id,
        transaction_type=data['transaction_type'],
        quantity=quantity,
        nav=nav,
        transaction_date=transaction_date,
        fees=data.get('fees', 0),
        notes=data.get('notes'),
        transfer_to_account_id=data.get('transfer_to_account_id'),
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 201


@bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Update a mutual fund transaction."""
    transaction = MutualFundTransaction.query.get_or_404(transaction_id)
    data = request.get_json()

    if 'account_id' in data:
        account = Account.query.get(data['account_id'])
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        transaction.account_id = data['account_id']
    if 'fund_id' in data:
        fund = MutualFund.query.get(data['fund_id'])
        if not fund:
            return jsonify({'error': 'Mutual fund not found'}), 404
        transaction.fund_id = data['fund_id']
    if 'transaction_type' in data:
        if data['transaction_type'] not in TRANSACTION_TYPES:
            return jsonify({'error': 'transaction_type must be BUY, SELL, or TRANSFER'}), 400
        transaction.transaction_type = data['transaction_type']
    if 'transaction_date' in data:
        try:
            transaction.transaction_date = _parse_datetime(data['transaction_date'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    if 'quantity' in data:
        transaction.quantity = data['quantity']
    if 'nav' in data:
        transaction.nav = data['nav']
    if 'fees' in data:
        transaction.fees = data['fees']
    if 'notes' in data:
        transaction.notes = data['notes']
    if 'transfer_to_account_id' in data:
        if data['transfer_to_account_id']:
            dest = Account.query.get(data['transfer_to_account_id'])
            if not dest:
                return jsonify({'error': 'Destination account not found'}), 404
        transaction.transfer_to_account_id = data['transfer_to_account_id']

    db.session.commit()
    return jsonify(transaction.to_dict())


@bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete a mutual fund transaction."""
    transaction = MutualFundTransaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Mutual fund transaction deleted successfully'}), 200


@bp.route('/transactions/bulk', methods=['POST'])
def create_bulk_transactions():
    """Create multiple mutual fund transactions (CSV/JSON bulk import).

    Each row accepts either ids (fund_id/account_id) or names
    (fund_name/scheme_code, account_name) for friendlier CSV uploads.
    """
    data = request.get_json()
    if not data or 'transactions' not in data or not isinstance(data['transactions'], list):
        return jsonify({'error': 'transactions array is required'}), 400

    rows = data['transactions']
    if not rows:
        return jsonify({'error': 'transactions array cannot be empty'}), 400

    created = []
    errors = []

    for idx, row in enumerate(rows):
        try:
            if 'transaction_type' not in row or row['transaction_type'] not in TRANSACTION_TYPES:
                errors.append({'row': idx + 1, 'error': 'transaction_type must be BUY, SELL, or TRANSFER'})
                continue
            if not row.get('transaction_date'):
                errors.append({'row': idx + 1, 'error': 'transaction_date is required'})
                continue

            account = _resolve_account(row)
            fund = _resolve_fund(row)
            if not account:
                errors.append({'row': idx + 1, 'error': 'Account not found (provide account_id or account_name)'})
                continue
            if not fund:
                errors.append({'row': idx + 1, 'error': 'Mutual fund not found (provide fund_id, scheme_code, or fund_name)'})
                continue

            dest_account = None
            if row['transaction_type'] == 'TRANSFER':
                dest_account = _resolve_destination_account(row)
                if not dest_account:
                    errors.append({'row': idx + 1, 'error': 'Destination account not found for TRANSFER'})
                    continue
                if dest_account.id == account.id:
                    errors.append({'row': idx + 1, 'error': 'transfer account must differ from account'})
                    continue

            transaction_date = _parse_datetime(row['transaction_date'])
            quantity, nav = _derive_units_nav(
                fund, row.get('quantity'), row.get('nav'), row.get('amount'), transaction_date,
                is_transfer=(row['transaction_type'] == 'TRANSFER'))

            transaction = MutualFundTransaction(
                account_id=account.id,
                fund_id=fund.id,
                transaction_type=row['transaction_type'],
                quantity=quantity,
                nav=nav,
                transaction_date=transaction_date,
                fees=row.get('fees', 0),
                notes=row.get('notes'),
                transfer_to_account_id=dest_account.id if dest_account else None,
            )
            db.session.add(transaction)
            created.append(transaction)
        except (ValueError, mf_nav.NavError) as e:
            msg = e.message if isinstance(e, mf_nav.NavError) else str(e)
            errors.append({'row': idx + 1, 'error': msg})
        except Exception as e:  # noqa: BLE001 - keep import going row by row
            errors.append({'row': idx + 1, 'error': str(e)})

    if created:
        db.session.commit()

    return jsonify({
        'success_count': len(created),
        'error_count': len(errors),
        'errors': errors,
        'created': [t.to_dict() for t in created],
    }), 201 if created else 400


# --------------------------------------------------------------------------
# NAV refresh
# --------------------------------------------------------------------------

def _apply_nav(fund, nav, nav_date):
    fund.nav = nav
    fund.nav_date = datetime.combine(nav_date, time.min) if isinstance(nav_date, datetime) else nav_date
    fund.last_updated = datetime.utcnow()


@bp.route('/navs/update/<string:scheme_code>', methods=['POST'])
def update_fund_nav(scheme_code):
    """Update NAV for one fund by AMFI scheme code."""
    fund = MutualFund.query.filter_by(scheme_code=scheme_code.upper()).first()
    if not fund:
        return jsonify({'error': 'Mutual fund not found for this scheme code'}), 404

    if fund.last_updated:
        elapsed = (datetime.utcnow() - fund.last_updated).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            return jsonify({
                'error': f'NAV was updated recently. Please wait {int(COOLDOWN_SECONDS - elapsed)} seconds.',
                'last_updated': fund.last_updated.isoformat() + 'Z',
                'nav': fund.nav,
            }), 429

    try:
        nav, date_str = mf_nav.fetch_latest_nav(fund.scheme_code)
        nav_date = datetime.strptime(date_str, '%Y-%m-%d')
    except mf_nav.NavError as e:
        return jsonify({
            'error': e.message,
            'hint': e.hint,
            'nav': fund.nav,
            'last_updated': fund.last_updated.isoformat() + 'Z' if fund.last_updated else None,
        }), e.status_code

    _apply_nav(fund, nav, nav_date)
    db.session.commit()
    return jsonify({'message': 'NAV updated', 'nav': fund.nav,
                    'nav_date': fund.nav_date.isoformat() + 'Z'})


@bp.route('/navs/update', methods=['POST'])
def update_all_navs():
    """Update NAV for all funds that have an AMFI scheme code."""
    funds = MutualFund.query.all()
    if not funds:
        return jsonify({'message': 'No mutual funds to update'}), 200

    updated = []
    failed = []
    rate_limited = False

    for i, fund in enumerate(funds):
        if not fund.scheme_code:
            failed.append({'name': fund.name, 'error': 'No AMFI scheme_code set'})
            continue
        if i > 0:
            time_module.sleep(1)  # be gentle with the free provider
        try:
            nav, date_str = mf_nav.fetch_latest_nav(fund.scheme_code)
            nav_date = datetime.strptime(date_str, '%Y-%m-%d')
            _apply_nav(fund, nav, nav_date)
            updated.append(fund.name)
        except mf_nav.NavError as e:
            if e.status_code == 429:
                rate_limited = True
                failed.append({'name': fund.name, 'error': 'Rate limit reached'})
                print(f'MF NAV rate limit hit at {fund.name}')
                break
            failed.append({'name': fund.name, 'error': e.message})

    db.session.commit()

    response = {
        'updated': updated,
        'failed': failed,
        'updated_count': len(updated),
        'failed_count': len(failed),
    }
    if rate_limited:
        response['warning'] = 'Rate limit reached. Please wait a few minutes before updating remaining funds.'
    return jsonify(response)
