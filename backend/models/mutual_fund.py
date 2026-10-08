from database import db
from datetime import datetime


class MutualFund(db.Model):
    """MutualFund model - represents an Indian mutual fund scheme (unit trust)"""

    __tablename__ = 'mutual_funds'

    id = db.Column(db.Integer, primary_key=True)
    scheme_code = db.Column(db.String(20), unique=True)  # AMFI scheme code (nullable for manual funds)
    name = db.Column(db.String(255), nullable=False)  # e.g. "HDFC Mid-Cap Opportunities Fund - Direct - Growth"
    amc = db.Column(db.String(100))  # Asset management company, e.g. "HDFC Mutual Fund"
    category = db.Column(db.String(100))  # SEBI category, e.g. "Equity: Mid Cap"
    plan = db.Column(db.String(20))  # 'DIRECT' or 'REGULAR'
    option = db.Column(db.String(20))  # 'GROWTH' or 'IDCW'
    isin = db.Column(db.String(20))
    folio = db.Column(db.String(50))
    currency = db.Column(db.String(3), default='INR')
    nav = db.Column(db.Float)  # Latest net asset value per unit
    nav_date = db.Column(db.DateTime)  # Date the latest NAV is for
    last_updated = db.Column(db.DateTime)  # When NAV was fetched
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    mutual_fund_transactions = db.relationship(
        'MutualFundTransaction',
        foreign_keys='MutualFundTransaction.fund_id',
        backref='fund',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'scheme_code': self.scheme_code,
            'name': self.name,
            'amc': self.amc,
            'category': self.category,
            'plan': self.plan,
            'option': self.option,
            'isin': self.isin,
            'folio': self.folio,
            'currency': self.currency or 'INR',
            'asset_class': 'MUTUAL_FUND',
            'nav': self.nav,
            'nav_date': self.nav_date.isoformat() + 'Z' if self.nav_date else None,
            'last_updated': self.last_updated.isoformat() + 'Z' if self.last_updated else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }

    def __repr__(self):
        return f'<MutualFund {self.scheme_code or self.name}>'
