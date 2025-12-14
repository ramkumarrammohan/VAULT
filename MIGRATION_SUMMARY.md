# Broker to Account Terminology Migration - Complete

## Summary
Successfully migrated the entire application from "Broker" terminology to "Account" terminology across the full stack.

## Changes Made

### Backend Changes

#### 1. Database Migration
- **File**: `backend/migrations/versions/5d77eb6e3225_rename_brokers_to_accounts.py`
- Renamed table: `brokers` → `accounts`
- Renamed columns in `holdings` table: `broker_id` → `account_id`
- Renamed columns in `transactions` table: `broker_id` → `account_id`
- Updated unique constraint: `unique_broker_stock` → `unique_account_stock`
- Migration successfully applied

#### 2. Models
- **File**: `backend/models/broker.py` → `backend/models/account.py`
  - Renamed class: `Broker` → `Account`
  - Updated table name: `'brokers'` → `'accounts'`
  
- **File**: `backend/models/holding.py`
  - Changed foreign key: `broker_id` → `account_id`
  - Updated relationship: `broker` → `account`
  - Updated `to_dict()`: `broker_name` → `account_name`
  
- **File**: `backend/models/transaction.py`
  - Changed foreign key: `broker_id` → `account_id`
  - Updated relationship: `broker` → `account`
  - Updated `to_dict()`: `broker_name` → `account_name`

#### 3. API Endpoints
- **File**: `backend/api/brokers.py` → `backend/api/accounts.py`
  - Renamed blueprint: `'brokers'` → `'accounts'`
  - Updated all route paths: `/brokers/` → `/accounts/`
  - Changed all variable names: `broker` → `account`
  
- **File**: `backend/api/holdings.py`
  - Updated imports: `from models.broker` → `from models.account`
  - Changed references: `Broker` → `Account`
  - Updated parameters: `broker_id` → `account_id`
  
- **File**: `backend/api/transactions.py`
  - Updated imports and model references
  - Changed parameters: `broker_id` → `account_id`
  - Updated validation to use `Account` model
  
- **File**: `backend/api/portfolio.py`
  - Renamed function parameter in grouping logic
  - Updated endpoint: `/by-broker` → `/by-account`
  - Changed response keys: `broker_id`, `broker_name` → `account_id`, `account_name`

#### 4. Application Setup
- **File**: `backend/app.py`
  - Updated imports: `from models import account` (instead of broker)
  - Changed blueprint registration: `accounts.bp` at `/api/accounts`

### Frontend Changes

#### 1. TypeScript Types
- **File**: `frontend/src/types/index.ts`
  - Renamed interface: `Broker` → `Account`
  - Updated `Holding` interface: `broker_id` → `account_id`, `broker_name` → `account_name`
  - Updated `PortfolioSummary`: `brokers_count` → `accounts_count`
  - Renamed interface: `BrokerSummary` → `AccountSummary`
  - Updated `Transaction` interface: `broker_id` → `account_id`, `broker_name` → `account_name`

#### 2. API Service
- **File**: `frontend/src/services/api.ts`
  - Renamed export: `brokerApi` → `accountApi`
  - Updated all endpoints: `/brokers/` → `/accounts/`
  - Updated portfolio API: `getByBroker()` → `getByAccount()`
  - Updated transaction API params: `broker_id` → `account_id`

#### 3. Vue Components

##### New Files Created:
- `frontend/src/views/AccountsView.vue` (replaces BrokersView.vue)
  - Updated all UI text: "Brokers" → "Accounts"
  - Changed API calls to use `accountApi`
  - Updated variable names throughout
  
- `frontend/src/views/AccountFormView.vue` (replaces BrokerFormView.vue)
  - Updated form labels and placeholders
  - Changed API calls to use `accountApi`
  - Updated all references and error messages

##### Updated Files:
- **`frontend/src/views/TransactionsView.vue`**
  - Changed imports: `brokerApi` → `accountApi`, `Broker` → `Account`
  - Updated state: `brokers` → `accounts`, `selectedBrokerId` → `selectedAccountId`
  - Changed form data: `broker_id` → `account_id`
  - Updated all functions: `loadBrokers()` → `loadAccounts()`
  - Changed UI labels: "Broker" → "Account"
  - Updated table header and dropdown labels
  
- **`frontend/src/views/DashboardView.vue`**
  - Updated summary card: "brokers" → "accounts"
  - Changed table header: "Broker" → "Account"
  - Updated data display: `broker_name` → `account_name`
  
- **`frontend/src/views/HoldingFormView.vue`**
  - Changed imports: `brokerApi` → `accountApi`, `Broker` → `Account`
  - Updated state: `brokers` → `accounts`
  - Changed form data: `broker_id` → `account_id`
  - Updated form label: "Broker" → "Account"
  - Changed helper link: `/brokers/add` → `/accounts/add`

#### 4. Router Configuration
- **File**: `frontend/src/router/index.ts`
  - Updated imports: `BrokersView` → `AccountsView`, `BrokerFormView` → `AccountFormView`
  - Changed route paths: `/brokers` → `/accounts`
  - Updated route names: `brokers`, `broker-add`, `broker-edit` → `accounts`, `account-add`, `account-edit`

#### 5. Navigation
- **File**: `frontend/src/App.vue`
  - Updated navbar link: "Brokers" → "Accounts"
  - Changed route: `/brokers` → `/accounts`

## Testing Checklist

### Backend
- [x] Migration applied successfully
- [x] Backend server starts without errors
- [x] `/api/accounts/` endpoints accessible
- [ ] CRUD operations work for accounts
- [ ] Transactions use account_id correctly
- [ ] Holdings use account_id correctly
- [ ] Portfolio calculations work with accounts

### Frontend
- [x] Frontend compiles without errors
- [x] Router configured correctly
- [x] TypeScript types updated
- [ ] Accounts page loads and displays data
- [ ] Account CRUD operations work
- [ ] Transaction form uses account selection
- [ ] Dashboard displays account information
- [ ] Holdings form uses account selection

## Database Schema (After Migration)

### accounts table
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### holdings table
```sql
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    quantity FLOAT NOT NULL,
    average_price FLOAT NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (id),
    FOREIGN KEY (stock_id) REFERENCES stocks (id),
    CONSTRAINT unique_account_stock UNIQUE (account_id, stock_id)
);
```

### transactions table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    transaction_type VARCHAR(4) NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    fees FLOAT DEFAULT 0,
    total_value FLOAT NOT NULL,
    transaction_date DATETIME NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (id),
    FOREIGN KEY (stock_id) REFERENCES stocks (id)
);
```

## Old Files to Remove (Optional Cleanup)

After confirming the new files work correctly, these can be deleted:
- `frontend/src/views/BrokersView.vue`
- `frontend/src/views/BrokerFormView.vue`

## Notes

1. **Backward Compatibility**: The migration is reversible. The downgrade function in the migration file can revert all changes.

2. **Data Preservation**: All data is preserved during the migration. The `op.rename_table()` and `alter_column()` operations maintain all existing records.

3. **API Compatibility**: The API endpoint URLs have changed from `/api/brokers/` to `/api/accounts/`. Any external clients will need to update their endpoint references.

4. **Consistent Terminology**: The word "Account" now appears consistently across:
   - Database table and column names
   - Backend model classes and relationships
   - API endpoint paths and response keys
   - Frontend TypeScript interfaces
   - UI labels and text
   - Route paths and component names

## Completion Status

✅ **COMPLETE** - All broker terminology has been successfully migrated to account terminology throughout the entire application stack.
