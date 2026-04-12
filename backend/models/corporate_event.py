from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from database import db
import enum

class CorporateEventType(enum.Enum):
    SPLIT = "SPLIT"
    DEMERGER = "DEMERGER"
    MERGER = "MERGER"
    AMALGAMATION = "AMALGAMATION"
    DIVIDEND = "DIVIDEND"
    NAME_CHANGE = "NAME_CHANGE"

class CorporateEvent(db.Model):
    __tablename__ = 'corporate_events'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    event_type = Column(Enum(CorporateEventType), nullable=False)
    event_date = Column(Date, nullable=False)
    ratio = Column(Float, nullable=True)  # For splits/mergers
    quantity = Column(Float, nullable=True)  # For demergers/bonus
    amount = Column(Float, nullable=True)  # For dividends
    related_stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=True)  # For mergers/amalgamations
    parent_cost_pct = Column(Float, nullable=True)  # e.g., 86.49 for ITC after demerger
    demerged_cost_pct = Column(Float, nullable=True)  # e.g., 13.51 for ITC Hotels after demerger
    notes = Column(Text, nullable=True)

    stock = relationship('Stock', foreign_keys=[stock_id])
    related_stock = relationship('Stock', foreign_keys=[related_stock_id])
