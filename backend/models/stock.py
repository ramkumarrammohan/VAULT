from database import db
from datetime import datetime


class Stock(db.Model):
    """Stock model - represents individual stocks"""
    
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    exchange = db.Column(db.String(50))  # NSE, BSE, NYSE, NASDAQ, etc.
    sector = db.Column(db.String(100))
    current_price = db.Column(db.Float)
    last_updated = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    holdings = db.relationship('Holding', backref='stock', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', 
                                   foreign_keys='Transaction.stock_id',
                                   backref='stock', 
                                   lazy=True, 
                                   cascade='all, delete-orphan')
    # Transactions where this stock was the demerger source
    demerger_transactions = db.relationship('Transaction',
                                           foreign_keys='Transaction.demerger_source_stock_id',
                                           backref='demerger_source_stock',
                                           lazy=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'exchange': self.exchange,
            'sector': self.sector,
            'current_price': self.current_price,
            'last_updated': self.last_updated.isoformat() + 'Z' if self.last_updated else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'
