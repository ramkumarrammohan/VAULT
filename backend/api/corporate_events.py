from flask import Blueprint, request, jsonify, abort
from models.corporate_event import CorporateEvent, CorporateEventType
from models.stock import Stock
from database import db
from datetime import datetime

bp = Blueprint('corporate_events', __name__, url_prefix='/corporate-events')

# List all corporate events
def serialize_event(event):
    return {
        'id': event.id,
        'stock_id': event.stock_id,
        'stock_symbol': event.stock.symbol if event.stock else None,
        'event_type': event.event_type.name,
        'event_date': event.event_date.isoformat(),
        'ratio': event.ratio,
        'quantity': event.quantity,
        'amount': event.amount,
        'related_stock_id': event.related_stock_id,
        'related_stock_symbol': event.related_stock.symbol if event.related_stock else None,
        'parent_cost_pct': event.parent_cost_pct,
        'demerged_cost_pct': event.demerged_cost_pct,
        'notes': event.notes,
    }

@bp.route('/', methods=['GET'])
def list_events():
    events = CorporateEvent.query.order_by(CorporateEvent.event_date.desc()).all()
    return jsonify([serialize_event(e) for e in events])

@bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = CorporateEvent.query.get_or_404(event_id)
    return jsonify(serialize_event(event))

@bp.route('/', methods=['POST'])
def create_event():
    data = request.json
    try:
        # Parse event_date string to Python date object
        event_date = data['event_date']
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        event = CorporateEvent(
            stock_id=data['stock_id'],
            event_type=CorporateEventType[data['event_type']],
            event_date=event_date,
            ratio=data.get('ratio'),
            quantity=data.get('quantity'),
            amount=data.get('amount'),
            related_stock_id=data.get('related_stock_id'),
            parent_cost_pct=data.get('parent_cost_pct'),
            demerged_cost_pct=data.get('demerged_cost_pct'),
            notes=data.get('notes'),
        )
        db.session.add(event)
        db.session.commit()
        return jsonify(serialize_event(event)), 201
    except Exception as e:
        db.session.rollback()
        abort(400, str(e))

@bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    event = CorporateEvent.query.get_or_404(event_id)
    data = request.json
    try:
        event.stock_id = data.get('stock_id', event.stock_id)
        if 'event_type' in data:
            event.event_type = CorporateEventType[data['event_type']]
        if 'event_date' in data:
            event_date = data['event_date']
            if isinstance(event_date, str):
                event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
            event.event_date = event_date
        event.ratio = data.get('ratio', event.ratio)
        event.quantity = data.get('quantity', event.quantity)
        event.amount = data.get('amount', event.amount)
        event.related_stock_id = data.get('related_stock_id', event.related_stock_id)
        event.parent_cost_pct = data.get('parent_cost_pct', event.parent_cost_pct)
        event.demerged_cost_pct = data.get('demerged_cost_pct', event.demerged_cost_pct)
        event.notes = data.get('notes', event.notes)
        db.session.commit()
        return jsonify(serialize_event(event))
    except Exception as e:
        db.session.rollback()
        abort(400, str(e))

@bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = CorporateEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return '', 204
