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
  currency?: string
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
  currency?: string
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

export interface CurrencySummary {
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
}

export interface PortfolioSummary {
  by_currency: Record<string, CurrencySummary>
  holdings_count: number
  accounts_count: number
}

export interface ConsolidatedHolding {
  stock_id: number
  stock_symbol: string
  stock_name: string
  currency?: string
  current_price?: number
  quantity: number
  average_price: number
  invested_value: number
  current_value: number
  gain_loss: number
  gain_loss_percentage: number
  sub_holdings: Holding[]
}

export interface AccountSummary {
  account_id: number
  account_name: string
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
  by_currency: CurrencyAccountSummary[]
}

export interface CurrencyAccountSummary {
  currency: string
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
  transaction_type: 'BUY' | 'SELL' | 'SPLIT' | 'DEMERGER' | 'TRANSFER'
  quantity: number
  price: number
  fees: number
  total_value: number
  transaction_date: string
  notes?: string
  created_at?: string
  transfer_to_account_id?: number | null
  transfer_to_account_name?: string | null
}

export interface CorporateEvent {
  id?: number
  stock_id: number
  stock_symbol?: string
  event_type: string
  event_date: string
  ratio?: number | null
  related_stock_id?: number | null
  related_stock_symbol?: string
  parent_cost_pct?: number | null
  demerged_cost_pct?: number | null
  notes?: string
}

// ---------------- Mutual Funds ----------------

export interface MutualFund {
  id: number
  scheme_code?: string
  name: string
  amc?: string
  category?: string
  plan?: string
  option?: string
  isin?: string
  folio?: string
  currency?: string
  asset_class?: 'MUTUAL_FUND'
  nav?: number
  nav_date?: string
  last_updated?: string
  created_at?: string
  updated_at?: string
}

/** Fund row enriched with computed portfolio aggregates (from /mutual-funds/overview) */
export interface MutualFundOverview extends MutualFund {
  total_units: number
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
}

export interface MutualFundHolding {
  account_id: number
  account_name: string
  fund_id: number
  fund_name: string
  scheme_code?: string
  amc?: string
  category?: string
  asset_class: 'MUTUAL_FUND'
  currency: string
  quantity: number
  average_price: number
  current_price?: number
  invested_value: number
  current_value: number
  total_fees: number
  gain_loss: number
  gain_loss_percentage: number
}

export interface MutualFundTransaction {
  id: number
  account_id: number
  account_name?: string
  fund_id: number
  fund_name?: string
  fund_scheme_code?: string
  transaction_type: 'BUY' | 'SELL' | 'TRANSFER'
  quantity: number
  nav: number
  amount: number
  fees: number
  total_value: number
  transaction_date: string
  notes?: string
  created_at?: string
  transfer_to_account_id?: number | null
  transfer_to_account_name?: string | null
}

export interface MutualFundBucketSummary {
  label: string
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
}

export interface MutualFundSummary {
  total_invested: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_percentage: number
  holdings_count: number
  by_category: MutualFundBucketSummary[]
  by_amc: MutualFundBucketSummary[]
}

