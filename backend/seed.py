"""Seed sample accounts, stocks, and transactions for local testing."""

from app import create_app
from database import db
from models.account import Account
from models.holding import Holding
from models.stock import Stock
from models.transaction import Transaction
from models.corporate_event import CorporateEvent
from datetime import datetime, UTC


def seed_database():
    app = create_app()
    
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        Transaction.query.delete()
        CorporateEvent.query.delete()
        Holding.query.delete()
        Stock.query.delete()
        Account.query.delete()
        db.session.commit()
        
        # Create sample brokers
        print("Creating brokers...")
        accounts = [
            Account(name="Zerodha", description="Indian broker - NSE/BSE"),
            Account(name="Robinhood", description="US broker - NYSE/NASDAQ"),
            Account(name="Interactive Brokers", description="Global broker")
        ]
        
        for account in accounts:
            db.session.add(account)
        db.session.commit()
        print(f"Created {len(accounts)} brokers")

        accounts_by_name = {account.name: account for account in accounts}
        
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
            stock.last_updated = datetime.now(UTC).replace(tzinfo=None)
            db.session.add(stock)
        db.session.commit()
        print(f"Created {len(stocks)} stocks")

        stocks_by_symbol = {stock.symbol: stock for stock in stocks}
        
        # Create sample transactions.
        # Dashboard holdings are derived from transaction history, not seeded Holding rows.
        print("Creating transactions...")
        transactions = [
            Transaction(
                account_id=accounts_by_name["Zerodha"].id,
                stock_id=stocks_by_symbol["RELIANCE.NS"].id,
                transaction_type="BUY",
                quantity=10,
                price=2200.00,
                fees=15.00,
                transaction_date=datetime(2025, 1, 10, 10, 0, 0),
                notes="Initial Reliance position"
            ),
            Transaction(
                account_id=accounts_by_name["Zerodha"].id,
                stock_id=stocks_by_symbol["TCS.NS"].id,
                transaction_type="BUY",
                quantity=5,
                price=3400.00,
                fees=12.00,
                transaction_date=datetime(2025, 1, 18, 11, 15, 0),
                notes="Long-term TCS buy"
            ),
            Transaction(
                account_id=accounts_by_name["Zerodha"].id,
                stock_id=stocks_by_symbol["INFY.NS"].id,
                transaction_type="BUY",
                quantity=18,
                price=1450.00,
                fees=10.00,
                transaction_date=datetime(2025, 2, 4, 9, 45, 0),
                notes="Infosys accumulation"
            ),
            Transaction(
                account_id=accounts_by_name["Zerodha"].id,
                stock_id=stocks_by_symbol["INFY.NS"].id,
                transaction_type="SELL",
                quantity=3,
                price=1525.00,
                fees=8.00,
                transaction_date=datetime(2025, 3, 20, 14, 30, 0),
                notes="Partial profit booking"
            ),
            Transaction(
                account_id=accounts_by_name["Robinhood"].id,
                stock_id=stocks_by_symbol["AAPL"].id,
                transaction_type="BUY",
                quantity=20,
                price=150.00,
                fees=3.00,
                transaction_date=datetime(2025, 1, 8, 16, 0, 0),
                notes="Apple starter position"
            ),
            Transaction(
                account_id=accounts_by_name["Robinhood"].id,
                stock_id=stocks_by_symbol["MSFT"].id,
                transaction_type="BUY",
                quantity=10,
                price=340.00,
                fees=3.00,
                transaction_date=datetime(2025, 2, 11, 15, 0, 0),
                notes="Microsoft buy"
            ),
            Transaction(
                account_id=accounts_by_name["Robinhood"].id,
                stock_id=stocks_by_symbol["TSLA"].id,
                transaction_type="BUY",
                quantity=8,
                price=220.00,
                fees=4.00,
                transaction_date=datetime(2025, 2, 25, 13, 20, 0),
                notes="Tesla trade"
            ),
            Transaction(
                account_id=accounts_by_name["Interactive Brokers"].id,
                stock_id=stocks_by_symbol["HDFCBANK.NS"].id,
                transaction_type="BUY",
                quantity=25,
                price=1600.00,
                fees=18.00,
                transaction_date=datetime(2025, 1, 14, 10, 10, 0),
                notes="Core banking position"
            ),
            Transaction(
                account_id=accounts_by_name["Interactive Brokers"].id,
                stock_id=stocks_by_symbol["GOOGL"].id,
                transaction_type="BUY",
                quantity=12,
                price=130.00,
                fees=5.00,
                transaction_date=datetime(2025, 3, 5, 19, 0, 0),
                notes="Alphabet buy"
            )
        ]

        for transaction in transactions:
            db.session.add(transaction)
        db.session.commit()
        print(f"Created {len(transactions)} transactions")
        
        print("\n✅ Database seeded successfully!")
        print(f"   - {len(accounts)} brokers")
        print(f"   - {len(stocks)} stocks")
        print(f"   - {len(transactions)} transactions")
        print("\nYou can now access the application at http://localhost:5173")

if __name__ == '__main__':
    seed_database()
