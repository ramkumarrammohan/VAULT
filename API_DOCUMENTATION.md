# Portfolio Tracker API Documentation

Base URL: `http://localhost:5000/api`

---

## Authentication

Currently, no authentication is required. Authentication can be added as a middleware layer later.

---

## Accounts API

### Get All Accounts
```http
GET /api/accounts
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Zerodha",
    "description": "Indian broker - NSE/BSE",
    "created_at": "2024-12-14T10:30:00",
    "updated_at": "2024-12-14T10:30:00"
  }
]
```

### Create Account
```http
POST /api/accounts
Content-Type: application/json

{
  "name": "Zerodha",
  "description": "Indian broker - NSE/BSE"
}
```

### Update Account
```http
PUT /api/brokers/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Account
```http
DELETE /api/accounts/{id}
```

---

## Stocks API

### Get All Stocks
```http
GET /api/stocks
```

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "sector": "Technology",
    "current_price": 178.50,
    "last_updated": "2024-12-14T10:30:00",
    "created_at": "2024-12-14T10:30:00"
  }
]
```

### Create Stock
```http
POST /api/stocks
Content-Type: application/json

{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "current_price": 178.50
}
```

**Note:** Symbol will be automatically converted to uppercase.

### Update Stock
```http
PUT /api/stocks/{id}
Content-Type: application/json

{
  "current_price": 180.25
}
```

---

## Holdings API

### Get All Holdings
```http
GET /api/holdings
```

**Response:**
```json
[
  {
    "id": 1,
    "broker_id": 1,
    "broker_name": "Zerodha",
    "stock_id": 1,
    "stock_symbol": "AAPL",
    "stock_name": "Apple Inc.",
    "quantity": 10,
    "average_price": 150.00,
    "current_price": 178.50,
    "invested_value": 1500.00,
    "current_value": 1785.00,
    "gain_loss": 285.00,
    "gain_loss_percentage": 19.00,
    "notes": "Long term investment",
    "created_at": "2024-12-14T10:30:00",
    "updated_at": "2024-12-14T10:30:00"
  }
]
```

### Create Holding
```http
POST /api/holdings
Content-Type: application/json

{
  "broker_id": 1,
  "stock_id": 1,
  "quantity": 10,
  "average_price": 150.00,
  "notes": "Long term investment"
}
```

**Validation:**
- `broker_id`, `stock_id`, `quantity`, and `average_price` are required
- Broker and stock must exist
- Combination of broker_id and stock_id must be unique

### Update Holding
```http
PUT /api/holdings/{id}
Content-Type: application/json

{
  "quantity": 15,
  "average_price": 155.00,
  "notes": "Updated notes"
}
```

### Delete Holding
```http
DELETE /api/holdings/{id}
```

---

## Portfolio API

### Get Portfolio Summary
```http
GET /api/portfolio/summary
```

**Response:**
```json
{
  "total_invested": 50000.00,
  "total_current_value": 58500.00,
  "total_gain_loss": 8500.00,
  "total_gain_loss_percentage": 17.00,
  "holdings_count": 8,
  "brokers_count": 3
}
```

### Get Portfolio by Broker
```http
GET /api/portfolio/by-broker
```

**Response:**
```json
[
  {
    "broker_id": 1,
    "broker_name": "Zerodha",
    "total_invested": 25000.00,
    "total_current_value": 28500.00,
    "total_gain_loss": 3500.00,
    "total_gain_loss_percentage": 14.00,
    "holdings_count": 3
  }
]
```

### Get Top Performers
```http
GET /api/portfolio/top-performers
```

**Response:**
```json
{
  "top_gainers": [
    {
      "holding": { /* holding object */ },
      "gain_loss_percentage": 25.50
    }
  ],
  "top_losers": [
    {
      "holding": { /* holding object */ },
      "gain_loss_percentage": -5.20
    }
  ]
}
```

---

## Prices API

### Update Single Stock Price
```http
POST /api/prices/update/{symbol}
```

**Example:**
```http
POST /api/prices/update/AAPL
```

**Response:**
```json
{
  "symbol": "AAPL",
  "current_price": 178.50,
  "last_updated": "2024-12-14T10:30:00"
}
```

### Update All Stock Prices
```http
POST /api/prices/update-all
```

**Response:**
```json
{
  "updated": ["AAPL", "MSFT", "GOOGL"],
  "failed": [
    {
      "symbol": "INVALID",
      "error": "Price not available"
    }
  ],
  "updated_count": 3,
  "failed_count": 1
}
```

### Fetch Stock Info (without saving)
```http
GET /api/prices/fetch/{symbol}
```

**Example:**
```http
GET /api/prices/fetch/TSLA
```

**Response:**
```json
{
  "symbol": "TSLA",
  "name": "Tesla, Inc.",
  "current_price": 242.80,
  "exchange": "NASDAQ",
  "sector": "Consumer Cyclical",
  "market_cap": 769234000000,
  "currency": "USD"
}
```

---

## Stock Symbol Formats

### Indian Stocks
- **NSE**: Add `.NS` suffix - e.g., `RELIANCE.NS`, `TCS.NS`, `INFY.NS`
- **BSE**: Add `.BO` suffix - e.g., `RELIANCE.BO`

### US Stocks
- Use plain symbol - e.g., `AAPL`, `MSFT`, `GOOGL`, `TSLA`

### Other Markets
Refer to [yfinance documentation](https://github.com/ranaroussi/yfinance) for symbol formats for other exchanges.

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Name is required"
}
```

### 404 Not Found
```json
{
  "error": "Stock not found"
}
```

### 409 Conflict
```json
{
  "error": "Broker already exists"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to fetch stock price: Connection timeout"
}
```

---

## Rate Limits

No rate limits currently implemented. Consider adding rate limiting for production use, especially for price update endpoints to avoid overwhelming the yfinance API.

---

## CORS

CORS is enabled for the following origins (configurable in `.env`):
- `http://localhost:5173` (Vue.js dev server)
- `http://localhost:3000` (alternative frontend)

---

## Future Endpoints (Not Yet Implemented)

### Transactions
- `GET /api/transactions` - List all transactions
- `POST /api/transactions` - Record new transaction
- `GET /api/holdings/{id}/transactions` - Get transactions for a holding

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Reports
- `GET /api/reports/performance` - Performance over time
- `GET /api/reports/allocation` - Asset allocation breakdown
- `GET /api/reports/export` - Export portfolio data (CSV/PDF)

---

## Corporate Events API

### Get All Corporate Events
```http
GET /api/corporate-events/
```
**Response:**
```json
[
  {
    "id": 1,
    "stock_id": 1,
    "stock_symbol": "AAPL",
    "event_type": "SPLIT",
    "event_date": "2026-04-01",
    "ratio": 2.0,
    "quantity": null,
    "amount": null,
    "related_stock_id": null,
    "related_stock_symbol": null,
    "notes": "2-for-1 split"
  }
]
```

### Get Corporate Event by ID
```http
GET /api/corporate-events/{id}
```
**Response:**
```json
{
  "id": 1,
  "stock_id": 1,
  "stock_symbol": "AAPL",
  "event_type": "SPLIT",
  "event_date": "2026-04-01",
  "ratio": 2.0,
  "quantity": null,
  "amount": null,
  "related_stock_id": null,
  "related_stock_symbol": null,
  "notes": "2-for-1 split"
}
```

### Create Corporate Event
```http
POST /api/corporate-events/
Content-Type: application/json

{
  "stock_id": 1,
  "event_type": "SPLIT",
  "event_date": "2026-04-01",
  "ratio": 2.0,
  "notes": "2-for-1 split"
}
```
**Response:**
```json
{
  "id": 2,
  "stock_id": 1,
  "stock_symbol": "AAPL",
  "event_type": "SPLIT",
  "event_date": "2026-04-01",
  "ratio": 2.0,
  "quantity": null,
  "amount": null,
  "related_stock_id": null,
  "related_stock_symbol": null,
  "notes": "2-for-1 split"
}
```

### Update Corporate Event
```http
PUT /api/corporate-events/{id}
Content-Type: application/json

{
  "ratio": 3.0,
  "notes": "3-for-1 split"
}
```
**Response:**
```json
{
  "id": 2,
  "stock_id": 1,
  "stock_symbol": "AAPL",
  "event_type": "SPLIT",
  "event_date": "2026-04-01",
  "ratio": 3.0,
  "quantity": null,
  "amount": null,
  "related_stock_id": null,
  "related_stock_symbol": null,
  "notes": "3-for-1 split"
}
```

### Delete Corporate Event
```http
DELETE /api/corporate-events/{id}
```
**Response:**
```
204 No Content
```

**Error Responses:**
- 400 Bad Request: Invalid data or missing required fields
- 404 Not Found: Event not found

---

## Transactions API

### Get All Transactions
```http
GET /api/transactions
```
**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "stock_id": 1,
    "transaction_type": "BUY",
    "quantity": 10,
    "price": 150.00,
    "transaction_date": "2026-04-01T10:00:00",
    "fees": 10.0,
    "notes": "Initial buy",
    "created_at": "2026-04-01T10:00:00"
  }
]
```

### Create Transaction
```http
POST /api/transactions
Content-Type: application/json

{
  "account_id": 1,
  "stock_id": 1,
  "transaction_type": "BUY",
  "quantity": 10,
  "price": 150.00,
  "transaction_date": "2026-04-01T10:00:00",
  "fees": 10.0,
  "notes": "Initial buy"
}
```
**Response:**
```json
{
  "id": 2,
  "account_id": 1,
  "stock_id": 1,
  "transaction_type": "BUY",
  "quantity": 10,
  "price": 150.00,
  "transaction_date": "2026-04-01T10:00:00",
  "fees": 10.0,
  "notes": "Initial buy",
  "created_at": "2026-04-01T10:00:00"
}
```

### Update Transaction
```http
PUT /api/transactions/{id}
Content-Type: application/json

{
  "quantity": 12,
  "price": 155.00,
  "notes": "Updated quantity"
}
```
**Response:**
```json
{
  "id": 2,
  "account_id": 1,
  "stock_id": 1,
  "transaction_type": "BUY",
  "quantity": 12,
  "price": 155.00,
  "transaction_date": "2026-04-01T10:00:00",
  "fees": 10.0,
  "notes": "Updated quantity",
  "created_at": "2026-04-01T10:00:00"
}
```

### Delete Transaction
```http
DELETE /api/transactions/{id}
```
**Response:**
```
204 No Content
```

**Error Responses:**
- 400 Bad Request: Invalid data or missing required fields
- 404 Not Found: Transaction not found
- 409 Conflict: Duplicate or conflicting transaction

---

## Testing with curl

### Create a complete holding workflow

```powershell
# 1. Create a broker
curl -X POST http://localhost:5000/api/brokers -H "Content-Type: application/json" -d '{\"name\":\"My Broker\",\"description\":\"Test broker\"}'

# 2. Fetch stock info (to verify symbol)
curl http://localhost:5000/api/prices/fetch/AAPL

# 3. Create a stock
curl -X POST http://localhost:5000/api/stocks -H "Content-Type: application/json" -d '{\"symbol\":\"AAPL\",\"name\":\"Apple Inc.\",\"exchange\":\"NASDAQ\",\"sector\":\"Technology\",\"current_price\":178.50}'

# 4. Create a holding
curl -X POST http://localhost:5000/api/holdings -H "Content-Type: application/json" -d '{\"broker_id\":1,\"stock_id\":1,\"quantity\":10,\"average_price\":150.00}'

# 5. Get portfolio summary
curl http://localhost:5000/api/portfolio/summary
```

---

## Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "message": "Portfolio Tracker API is running"
}
```
