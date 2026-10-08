// Corporate Events API
export const corporateEventApi = {
  getAll: () => apiClient.get('/corporate-events/'),
  getById: (id: number) => apiClient.get(`/corporate-events/${id}`),
  create: (data: any) => apiClient.post('/corporate-events/', data),
  update: (id: number, data: any) => apiClient.put(`/corporate-events/${id}`, data),
  delete: (id: number) => apiClient.delete(`/corporate-events/${id}`)
}
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Accounts API
export const accountApi = {
  getAll: () => apiClient.get('/accounts/'),
  getById: (id: number) => apiClient.get(`/accounts/${id}`),
  create: (data: any) => apiClient.post('/accounts/', data),
  update: (id: number, data: any) => apiClient.put(`/accounts/${id}`, data),
  delete: (id: number) => apiClient.delete(`/accounts/${id}`)
}

// Stocks API
export const stockApi = {
  getAll: () => apiClient.get('/stocks/'),
  getById: (id: number) => apiClient.get(`/stocks/${id}`),
  create: (data: any) => apiClient.post('/stocks/', data),
  update: (id: number, data: any) => apiClient.put(`/stocks/${id}`, data),
  delete: (id: number) => apiClient.delete(`/stocks/${id}`),
  fetchInfo: (symbol: string) => apiClient.get(`/prices/fetch/${symbol}`)
}

// Portfolio API
export const portfolioApi = {
  getHoldings: () => apiClient.get('/portfolio/holdings'),
  getSummary: () => apiClient.get('/portfolio/summary'),
  getByAccount: () => apiClient.get('/portfolio/by-account'),
  getTopPerformers: () => apiClient.get('/portfolio/top-performers')
}

// Prices API
export const priceApi = {
  updatePrice: (symbol: string) => apiClient.post(`/prices/update/${symbol}`),
  updateAllPrices: () => apiClient.post('/prices/update-all')
}

// Transactions API
export const transactionApi = {
  getAll: (params?: { account_id?: number; stock_id?: number }) => apiClient.get('/transactions/', { params }),
  getById: (id: number) => apiClient.get(`/transactions/${id}`),
  create: (data: any) => apiClient.post('/transactions/', data),
  createBulk: (data: any) => apiClient.post('/transactions/bulk', data),
  update: (id: number, data: any) => apiClient.put(`/transactions/${id}`, data),
  delete: (id: number) => apiClient.delete(`/transactions/${id}`)
}

// Mutual Funds API
export const mutualFundApi = {
  getAll: () => apiClient.get('/mutual-funds/'),
  getOverview: () => apiClient.get('/mutual-funds/overview'),
  getById: (id: number) => apiClient.get(`/mutual-funds/${id}`),
  create: (data: any) => apiClient.post('/mutual-funds/', data),
  update: (id: number, data: any) => apiClient.put(`/mutual-funds/${id}`, data),
  delete: (id: number) => apiClient.delete(`/mutual-funds/${id}`),
  searchSchemes: (query: string) => apiClient.get('/mutual-funds/search', { params: { q: query } }),
  getScheme: (schemeCode: string) => apiClient.get(`/mutual-funds/scheme/${schemeCode}`),
  getHoldings: () => apiClient.get('/mutual-funds/holdings'),
  getSummary: () => apiClient.get('/mutual-funds/summary'),
  getTransactions: (params?: { account_id?: number; fund_id?: number }) =>
    apiClient.get('/mutual-funds/transactions', { params }),
  createTransaction: (data: any) => apiClient.post('/mutual-funds/transactions', data),
  createBulkTransactions: (data: any) => apiClient.post('/mutual-funds/transactions/bulk', data),
  updateTransaction: (id: number, data: any) => apiClient.put(`/mutual-funds/transactions/${id}`, data),
  deleteTransaction: (id: number) => apiClient.delete(`/mutual-funds/transactions/${id}`),
  updateNav: (schemeCode: string) => apiClient.post(`/mutual-funds/navs/update/${schemeCode}`),
  updateAllNavs: () => apiClient.post('/mutual-funds/navs/update')
}

export default apiClient
