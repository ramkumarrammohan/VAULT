from flask import Flask
from flask_cors import CORS
from config.config import config
from database import db, migrate
import os


def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Import models (needed for migrations)
    from models import account, stock, holding, transaction, corporate_event
    
    # Register blueprints
    from api import accounts, stocks, holdings, portfolio, prices, transactions, corporate_events

    app.register_blueprint(accounts.bp, url_prefix=f"{app.config['API_PREFIX']}/accounts")
    app.register_blueprint(stocks.bp, url_prefix=f"{app.config['API_PREFIX']}/stocks")
    app.register_blueprint(holdings.bp, url_prefix=f"{app.config['API_PREFIX']}/holdings")
    app.register_blueprint(portfolio.bp, url_prefix=f"{app.config['API_PREFIX']}/portfolio")
    app.register_blueprint(prices.bp, url_prefix=f"{app.config['API_PREFIX']}/prices")
    app.register_blueprint(transactions.bp, url_prefix=f"{app.config['API_PREFIX']}/transactions")
    app.register_blueprint(corporate_events.bp, url_prefix=f"{app.config['API_PREFIX']}/corporate-events")
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'Portfolio Tracker API is running'}
    
    return app


if __name__ == '__main__':
    print('creating the application...')
    app = create_app()
    print('starting the application...')
    app.run(debug=True, port=5000)
