export interface Account {
  id: number
  name: string
  description?: string
  created_at?: string
  updated_at?: string
}

export interface Stock {
  id: number
  symbol: string
  name: string
  exchange?: string
  sector?: string
  current_price?: number
  last_updated?: string
  created_at?: string
}

export interface Holding {
  id: number
  account_id: number
  account_name: string
  stock_id: number
  stock_symbol: string
  stock_name: string
  quantity: number
  average_price: number
  current_price?: number
  invested_value: number
  current_value: number
  gain_loss: number
  gain_loss_percentage: number
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface PortfolioSummary {
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
  accounts_count: number
}

export interface AccountSummary {
  account_id: number
  account_name: string
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
}

export interface Transaction {
  id: number
  account_id: number
  account_name: string
  stock_id: number
  stock_symbol: string
  transaction_type: 'BUY' | 'SELL'
  quantity: number
  price: number
  fees: number
  total_value: number
  transaction_date: string
  notes?: string
  created_at?: string
}
