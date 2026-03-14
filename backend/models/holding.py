from database import db
from datetime import datetime


class Holding(db.Model):
    """Holding model - represents stock holdings at a specific account"""
    
    __tablename__ = 'holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    average_price = db.Column(db.Float, nullable=False)  # Average purchase price
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique combination of account and stock
    __table_args__ = (
        db.UniqueConstraint('account_id', 'stock_id', name='unique_account_stock'),
    )
    
    def to_dict(self):
        """Convert model to dictionary with calculated fields"""
        invested_value = self.quantity * self.average_price
        current_value = self.quantity * (self.stock.current_price or 0)
        gain_loss = current_value - invested_value
        gain_loss_percentage = (gain_loss / invested_value * 100) if invested_value > 0 else 0
        
        return {
            'id': self.id,
            'account_id': self.account_id,
            'account_name': self.account.name,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol,
            'stock_name': self.stock.name,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'current_price': self.stock.current_price,
            'invested_value': round(invested_value, 2),
            'current_value': round(current_value, 2),
            'gain_loss': round(gain_loss, 2),
            'gain_loss_percentage': round(gain_loss_percentage, 2),
            'notes': self.notes,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Holding {self.stock.symbol} at {self.account.name}>'
