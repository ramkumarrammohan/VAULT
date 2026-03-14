from database import db
from datetime import datetime


class Transaction(db.Model):
    """Transaction model - records buy/sell transactions for stocks"""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'BUY', 'SELL', 'SPLIT', 'DEMERGER'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    fees = db.Column(db.Float, default=0)  # Account fees, taxes, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Demerger specific fields
    demerger_source_stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=True)  # Parent stock for demerger
    demerger_ratio = db.Column(db.Float, nullable=True)  # Ratio like 1:1 or 1:0.5
    
    # Relationships
    account = db.relationship('Account', backref='transactions')
    # Note: stock and demerger_source_stock relationships are defined via backref from Stock model
    
    def to_dict(self):
        """Convert model to dictionary"""
        total_value = self.quantity * self.price + self.fees
        
        result = {
            'id': self.id,
            'account_id': self.account_id,
            'account_name': self.account.name,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price': self.price,
            'fees': self.fees,
            'total_value': round(total_value, 2),
            'transaction_date': self.transaction_date.isoformat() + 'Z' if self.transaction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'demerger_source_stock_id': self.demerger_source_stock_id,
            'demerger_ratio': self.demerger_ratio
        }
        
        # Add source stock symbol if it's a demerger
        if self.demerger_source_stock_id:
            from models.stock import Stock
            source_stock = Stock.query.get(self.demerger_source_stock_id)
            if source_stock:
                result['demerger_source_stock_symbol'] = source_stock.symbol
        
        return result
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.quantity} {self.stock.symbol}>'
