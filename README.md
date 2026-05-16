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

## Docker — Production Deployment

### 1. Build & Push Images (local machine)

Run these after every code change:

```powershell
# Build
docker build -t ramkumarrammohan/vault-backend:latest ./backend
docker build -t ramkumarrammohan/vault-frontend:latest ./frontend

# Push to Docker Hub
docker login
docker push ramkumarrammohan/vault-backend:latest
docker push ramkumarrammohan/vault-frontend:latest
```

### 2. First-Time Server Setup

```bash
# Create MySQL data directory
mkdir -p /home/ramkumar/Data/VAULT_DATA

# Copy required files to server (no source code needed)
scp docker-compose.yml backend/.env.prod user@<server-ip>:~/vault/

# SSH into server
ssh user@<server-ip>
cd ~/vault

# Start all containers
docker compose up -d

# Verify all 3 containers are running
docker compose ps
```

### 3. Verify Deployment

```bash
curl http://localhost/health          # {"status": "ok"}
curl http://localhost/api/accounts/   # returns JSON
```

### 4. Redeploy After Code Changes

```bash
# On the server — pull latest images and restart
docker compose pull && docker compose up -d
```

### 5. Useful Operations

```bash
# View live logs
docker compose logs -f

# View backend logs only
docker compose logs backend --tail 50

# View MySQL logs
docker compose logs vault_db --tail 20

# Run database seed
docker compose exec backend python seed.py

# Stop all containers
docker compose down

# Stop and wipe MySQL data volume (destructive)
docker compose down -v
```

> **Note:** `backend/.env.prod` contains secrets — never commit it to git.
> Add it to `.gitignore` and copy it to the server separately.

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
