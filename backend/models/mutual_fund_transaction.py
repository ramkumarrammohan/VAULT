from database import db
from datetime import datetime


class MutualFundTransaction(db.Model):
    """MutualFundTransaction model - buy/sell/transfer of mutual fund units.

    Uses the same transaction_type convention as the stock Transaction model:
    'BUY' (lumpsum or SIP purchase at NAV), 'SELL' (redemption), 'TRANSFER'
    (move units between accounts preserving cost basis).
    """

    __tablename__ = 'mutual_fund_transactions'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('mutual_funds.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'BUY', 'SELL', 'TRANSFER'
    quantity = db.Column(db.Float, nullable=False)  # Units purchased/sold (3-4 dp precision)
    nav = db.Column(db.Float, nullable=False)  # NAV per unit at transaction date
    transaction_date = db.Column(db.DateTime, nullable=False)
    fees = db.Column(db.Float, default=0)  # Exit load / transaction charges
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Transfer specific field (destination account)
    transfer_to_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)

    # Relationships (no backref added to Account so the equity Account model stays untouched)
    account = db.relationship('Account', foreign_keys=[account_id])
    transfer_to_account = db.relationship('Account', foreign_keys=[transfer_to_account_id])

    def to_dict(self):
        """Convert model to dictionary"""
        amount = self.quantity * self.nav
        total_value = amount + self.fees

        return {
            'id': self.id,
            'account_id': self.account_id,
            'account_name': self.account.name if self.account else None,
            'fund_id': self.fund_id,
            'fund_name': self.fund.name if self.fund else None,
            'fund_scheme_code': self.fund.scheme_code if self.fund else None,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'nav': self.nav,
            'amount': round(amount, 2),
            'fees': self.fees,
            'total_value': round(total_value, 2),
            'transaction_date': self.transaction_date.isoformat() + 'Z' if self.transaction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'transfer_to_account_id': self.transfer_to_account_id,
            'transfer_to_account_name': self.transfer_to_account.name if self.transfer_to_account else None,
        }

    def __repr__(self):
        return f'<MutualFundTransaction {self.transaction_type} {self.quantity} {self.fund.name if self.fund else ""}>'
