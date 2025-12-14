# Portfolio Tracker - Quick Start Guide

## ✅ Implementation Complete!

Your personal portfolio tracker MVP is now fully set up with:
- Flask backend API (Python)
- Vue.js frontend (TypeScript)
- SQLite database with migrations
- Stock price integration via yfinance
- Sample data loaded

---

## 🚀 Running the Application

### Backend (Flask API)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

The API will run at: **http://localhost:5000**

### Frontend (Vue.js)

Open a new terminal:

```powershell
cd frontend
npm run dev
```

The app will run at: **http://localhost:5173**

---

## 📊 What's Implemented

### Backend API Endpoints

#### Brokers
- `GET /api/brokers` - List all brokers
- `POST /api/brokers` - Create new broker
- `GET /api/brokers/{id}` - Get broker details
- `PUT /api/brokers/{id}` - Update broker
- `DELETE /api/brokers/{id}` - Delete broker

#### Stocks
- `GET /api/stocks` - List all stocks
- `POST /api/stocks` - Add new stock
- `GET /api/stocks/{id}` - Get stock details
- `PUT /api/stocks/{id}` - Update stock
- `DELETE /api/stocks/{id}` - Delete stock

#### Holdings
- `GET /api/holdings` - List all holdings
- `POST /api/holdings` - Create new holding
- `GET /api/holdings/{id}` - Get holding details
- `PUT /api/holdings/{id}` - Update holding
- `DELETE /api/holdings/{id}` - Delete holding

#### Portfolio
- `GET /api/portfolio/summary` - Overall portfolio summary
- `GET /api/portfolio/by-broker` - Portfolio grouped by broker
- `GET /api/portfolio/top-performers` - Top gainers/losers

#### Prices
- `POST /api/prices/update/{symbol}` - Update price for one stock
- `POST /api/prices/update-all` - Update all stock prices
- `GET /api/prices/fetch/{symbol}` - Fetch stock info from yfinance

### Frontend Features

1. **Dashboard View**
   - Portfolio summary cards (invested, current value, gain/loss)
   - Holdings table with real-time calculations
   - Update all prices button

2. **API Integration**
   - Axios-based API client
   - TypeScript type definitions
   - Environment-based configuration

---

## 🗂️ Project Structure

```
/backend
  /api                  # Flask blueprints for API endpoints
    brokers.py         # Broker CRUD operations
    stocks.py          # Stock CRUD operations
    holdings.py        # Holding CRUD operations
    portfolio.py       # Portfolio calculations
    prices.py          # Price update endpoints
  /models              # SQLAlchemy models
    broker.py
    stock.py
    holding.py
    transaction.py
  /config              # Configuration files
    config.py
  /migrations          # Alembic database migrations
  /venv                # Python virtual environment
  app.py               # Flask application factory
  seed.py              # Sample data seeder
  .env                 # Environment variables

/frontend
  /src
    /services          # API client
      api.ts
    /types             # TypeScript types
      index.ts
    /views             # Vue components
      DashboardView.vue
    /router            # Vue Router config
    App.vue            # Main app component
  .env                 # Environment variables
```

---

## 🧪 Testing with Sample Data

Sample data has been loaded with:
- **3 brokers**: Zerodha, Robinhood, Interactive Brokers
- **8 stocks**: Mix of Indian (NSE) and US (NASDAQ) stocks
- **8 holdings**: Distributed across brokers

To reload sample data:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python seed.py
```

---

## 🔧 Common Operations

### Add a New Holding

Using the API directly (or build a form in frontend):

```powershell
# First, create a stock if it doesn't exist
curl -X POST http://localhost:5000/api/stocks -H "Content-Type: application/json" -d '{
  "symbol": "NVDA",
  "name": "NVIDIA Corporation",
  "exchange": "NASDAQ",
  "sector": "Technology"
}'

# Then create a holding
curl -X POST http://localhost:5000/api/holdings -H "Content-Type: application/json" -d '{
  "broker_id": 2,
  "stock_id": 9,
  "quantity": 10,
  "average_price": 450.00
}'
```

### Update Stock Prices

Click "Update Prices" button in the dashboard, or use API:

```powershell
# Update all stocks
curl -X POST http://localhost:5000/api/prices/update-all

# Update specific stock
curl -X POST http://localhost:5000/api/prices/update/AAPL
```

### Database Migrations

After changing models:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
flask db migrate -m "Description of changes"
flask db upgrade
```

---

## 🔐 Authentication (Future Enhancement)

Authentication is designed to be plugged in later:
- API endpoints are structured to accept auth middleware
- Use Flask-JWT-Extended or Flask-Login
- Add authentication decorator to protected routes
- Update frontend API client to include auth headers

---

## 🌍 Stock Markets Supported

The yfinance integration supports multiple exchanges:
- **Indian**: Add `.NS` suffix (NSE) or `.BO` (BSE) - e.g., `RELIANCE.NS`
- **US**: Use plain symbol - e.g., `AAPL`, `MSFT`
- **Other**: Check yfinance documentation for symbol formats

---

## 📝 Next Steps (Beyond MVP)

1. **Add Forms**: Create Vue components for adding/editing brokers, stocks, holdings
2. **Charts**: Add Chart.js or similar for portfolio visualization
3. **Transactions**: Implement transaction tracking UI
4. **Authentication**: Add user login and multi-user support
5. **Real-time Updates**: WebSocket for live price updates
6. **Export**: CSV/PDF export of portfolio data
7. **Alerts**: Price alerts and notifications
8. **Mobile**: Responsive design improvements

---

## 🐛 Troubleshooting

### Backend not starting
- Ensure virtual environment is activated
- Check if port 5000 is available
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Frontend not starting
- Ensure Node.js is installed
- Run `npm install` in frontend directory
- Check if port 5173 is available

### CORS errors
- Verify backend CORS_ORIGINS in `.env` includes frontend URL
- Check that both servers are running

### Database errors
- Delete `portfolio.db` and `migrations/` folder, then reinitialize:
  ```powershell
  flask db init
  flask db migrate -m "Initial migration"
  flask db upgrade
  ```

---

## 📚 Technologies Used

- **Backend**: Flask, SQLAlchemy, Alembic, yfinance
- **Frontend**: Vue.js 3, TypeScript, Vue Router, Axios
- **Database**: SQLite (development) - easily switch to PostgreSQL for production
- **API**: RESTful architecture with Flask blueprints

---

Enjoy building your portfolio tracker! 🚀📈
