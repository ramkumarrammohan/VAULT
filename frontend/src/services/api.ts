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

export default apiClient
