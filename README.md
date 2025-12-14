# Portfolio Tracker

A personal portfolio tracker application for managing stock holdings across multiple brokers.

## Project Structure

```
/backend       - Flask REST API
  /api         - API endpoints (blueprints)
  /models      - SQLAlchemy database models
  /config      - Configuration files
  /migrations  - Alembic database migrations
  /venv        - Python virtual environment
/frontend      - Vue.js application
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create and activate Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Initialize database:
   ```powershell
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. Run the Flask development server:
   ```powershell
   flask run
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Run the Vue development server:
   ```powershell
   npm run dev
   ```

## Features (MVP)

- Track stock holdings across multiple brokers
- View portfolio summary (total value, gains/losses)
- Add/edit/delete stock holdings
- Fetch current stock prices
- Portfolio visualization

## Tech Stack

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-CORS
- **Frontend**: Vue.js 3, Vue Router, Axios
- **Database**: SQLite (development)
- **Stock Data**: yfinance
