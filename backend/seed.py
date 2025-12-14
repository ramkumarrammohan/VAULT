"""
Seed script to populate the database with sample data
Run this script to test the application with sample brokers, stocks, and holdings
"""

from app import create_app
from database import db
from models.broker import Broker
from models.stock import Stock
from models.holding import Holding
from datetime import datetime

def seed_database():
    app = create_app()
    
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        Holding.query.delete()
        Stock.query.delete()
        Broker.query.delete()
        db.session.commit()
        
        # Create sample brokers
        print("Creating brokers...")
        brokers = [
            Broker(name="Zerodha", description="Indian broker - NSE/BSE"),
            Broker(name="Robinhood", description="US broker - NYSE/NASDAQ"),
            Broker(name="Interactive Brokers", description="Global broker")
        ]
        
        for broker in brokers:
            db.session.add(broker)
        db.session.commit()
        print(f"Created {len(brokers)} brokers")
        
        # Create sample stocks
        print("Creating stocks...")
        stocks = [
            # Indian stocks
            Stock(symbol="RELIANCE.NS", name="Reliance Industries", exchange="NSE", sector="Energy", current_price=2450.50),
            Stock(symbol="TCS.NS", name="Tata Consultancy Services", exchange="NSE", sector="IT", current_price=3567.20),
            Stock(symbol="INFY.NS", name="Infosys", exchange="NSE", sector="IT", current_price=1543.75),
            Stock(symbol="HDFCBANK.NS", name="HDFC Bank", exchange="NSE", sector="Banking", current_price=1650.30),
            
            # US stocks
            Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", sector="Technology", current_price=178.50),
            Stock(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ", sector="Technology", current_price=380.25),
            Stock(symbol="GOOGL", name="Alphabet Inc.", exchange="NASDAQ", sector="Technology", current_price=142.75),
            Stock(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", sector="Automotive", current_price=242.80)
        ]
        
        for stock in stocks:
            stock.last_updated = datetime.utcnow()
            db.session.add(stock)
        db.session.commit()
        print(f"Created {len(stocks)} stocks")
        
        # Create sample holdings
        print("Creating holdings...")
        holdings = [
            # Zerodha holdings (Indian stocks)
            Holding(broker_id=1, stock_id=1, quantity=10, average_price=2200.00),  # RELIANCE
            Holding(broker_id=1, stock_id=2, quantity=5, average_price=3400.00),   # TCS
            Holding(broker_id=1, stock_id=3, quantity=15, average_price=1450.00),  # INFY
            
            # Robinhood holdings (US stocks)
            Holding(broker_id=2, stock_id=5, quantity=20, average_price=150.00),   # AAPL
            Holding(broker_id=2, stock_id=6, quantity=10, average_price=340.00),   # MSFT
            Holding(broker_id=2, stock_id=8, quantity=8, average_price=220.00),    # TSLA
            
            # Interactive Brokers holdings (mixed)
            Holding(broker_id=3, stock_id=4, quantity=25, average_price=1600.00),  # HDFCBANK
            Holding(broker_id=3, stock_id=7, quantity=12, average_price=130.00)    # GOOGL
        ]
        
        for holding in holdings:
            db.session.add(holding)
        db.session.commit()
        print(f"Created {len(holdings)} holdings")
        
        print("\n✅ Database seeded successfully!")
        print(f"   - {len(brokers)} brokers")
        print(f"   - {len(stocks)} stocks")
        print(f"   - {len(holdings)} holdings")
        print("\nYou can now access the application at http://localhost:5173")

if __name__ == '__main__':
    seed_database()
