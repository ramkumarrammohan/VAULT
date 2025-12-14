<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { stockApi, priceApi } from '@/services/api'
import type { Stock } from '@/types'

const router = useRouter()
const stocks = ref<Stock[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const refreshingStocks = ref<Set<number>>(new Set())

const loadStocks = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await stockApi.getAll()
    stocks.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load stocks'
    console.error('Error loading stocks:', err)
  } finally {
    loading.value = false
  }
}

const deleteStock = async (id: number, symbol: string) => {
  if (!confirm(`Are you sure you want to delete stock "${symbol}"? This will also delete all associated holdings.`)) {
    return
  }

  try {
    await stockApi.delete(id)
    await loadStocks()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to delete stock'
    console.error('Error deleting stock:', err)
  }
}

const refreshPrice = async (id: number, symbol: string) => {
  refreshingStocks.value.add(id)
  error.value = null

  try {
    await priceApi.updatePrice(symbol)
    await loadStocks()
  } catch (err: any) {
    error.value = err.response?.data?.error || `Failed to update price for ${symbol}`
    console.error('Error updating price:', err)
  } finally {
    refreshingStocks.value.delete(id)
  }
}

const isRefreshing = (id: number) => {
  return refreshingStocks.value.has(id)
}

const goToAdd = () => {
  router.push('/stocks/add')
}

const goToEdit = (id: number) => {
  router.push(`/stocks/edit/${id}`)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(value)
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadStocks()
})
</script>

<template>
  <div class="stocks-page">
    <div class="header">
      <h1>Manage Stocks</h1>
      <button @click="goToAdd" class="btn-primary">Add Stock</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="stocks.length === 0" class="empty-state">
      <p>No stocks yet. Add your first stock to get started!</p>
    </div>

    <div v-else class="stocks-table-container">
      <table class="stocks-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Exchange</th>
            <th>Sector</th>
            <th>Current Price</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in stocks" :key="stock.id">
            <td><strong>{{ stock.symbol }}</strong></td>
            <td>{{ stock.name }}</td>
            <td>{{ stock.exchange || 'N/A' }}</td>
            <td>{{ stock.sector || 'N/A' }}</td>
            <td>{{ stock.current_price ? formatCurrency(stock.current_price) : 'N/A' }}</td>
            <td>{{ formatDate(stock.last_updated) }}</td>
            <td class="actions">
              <button @click="refreshPrice(stock.id, stock.symbol)" class="btn-refresh" :disabled="isRefreshing(stock.id)">
                {{ isRefreshing(stock.id) ? 'Updating...' : 'Refresh' }}
              </button>
              <button @click="goToEdit(stock.id)" class="btn-secondary">Edit</button>
              <button @click="deleteStock(stock.id, stock.symbol)" class="btn-danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.stocks-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

h1 {
  font-size: 2rem;
  color: #2c3e50;
}

.btn-primary {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #359268;
}

.btn-refresh {
  background-color: #27ae60;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  margin-right: 0.5rem;
  transition: background-color 0.3s;
}

.btn-refresh:hover:not(:disabled) {
  background-color: #229954;
}

.btn-refresh:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-secondary {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  margin-right: 0.5rem;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #2980b9;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.3s;
}

.btn-danger:hover {
  background-color: #c0392b;
}

.error-message {
  background-color: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-size: 1.1rem;
}

.stocks-table-container {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.stocks-table {
  width: 100%;
  border-collapse: collapse;
}

.stocks-table th,
.stocks-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.stocks-table th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.stocks-table tbody tr:hover {
  background-color: #f9f9f9;
}

.stocks-table td strong {
  color: #2c3e50;
}

.stocks-table td.actions {
  white-space: nowrap;
}
</style>
