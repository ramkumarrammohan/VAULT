from database import db
from datetime import datetime


class Transaction(db.Model):
    """Transaction model - records buy/sell transactions for stocks"""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    fees = db.Column(db.Float, default=0)  # Account fees, taxes, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    account = db.relationship('Account', backref='transactions')
    
    def to_dict(self):
        """Convert model to dictionary"""
        total_value = self.quantity * self.price + self.fees
        
        return {
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
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.quantity} {self.stock.symbol}>'
