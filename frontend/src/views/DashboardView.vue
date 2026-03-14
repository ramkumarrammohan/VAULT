<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { portfolioApi, holdingApi, priceApi, accountApi, stockApi } from '@/services/api'
import type { PortfolioSummary, Holding, Account, Stock } from '@/types'

const summary = ref<PortfolioSummary | null>(null)
const holdings = ref<Holding[]>([])
const accounts = ref<Account[]>([])
const stocks = ref<Stock[]>([])
const selectedAccountId = ref<number | null>(null)
const selectedStockId = ref<number | null>(null)
const sortBy = ref<string>('stock_symbol')
const sortDirection = ref<'asc' | 'desc'>('asc')
const loading = ref(false)
const updating = ref(false)

const loadAccounts = async () => {
  try {
    const response = await accountApi.getAll()
    accounts.value = response.data
  } catch (error) {
    console.error('Error loading accounts:', error)
  }
}

const loadStocks = async () => {
  try {
    const response = await stockApi.getAll()
    stocks.value = response.data
  } catch (error) {
    console.error('Error loading stocks:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const [summaryRes, holdingsRes] = await Promise.all([
      portfolioApi.getSummary(),
      portfolioApi.getHoldings()
    ])
    summary.value = summaryRes.data
    holdings.value = holdingsRes.data
  } catch (error) {
    console.error('Error loading data:', error)
  } finally {
    loading.value = false
  }
}

const updateAllPrices = async () => {
  updating.value = true
  try {
    await priceApi.updateAllPrices()
    await loadData()
  } catch (error) {
    console.error('Error updating prices:', error)
  } finally {
    updating.value = false
  }
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2
  }).format(value)
}

const getGainLossClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const filteredHoldings = computed(() => {
  let filtered = holdings.value

  if (selectedAccountId.value) {
    filtered = filtered.filter(h => h.account_id === selectedAccountId.value)
  }

  if (selectedStockId.value) {
    filtered = filtered.filter(h => h.stock_id === selectedStockId.value)
  }

  return filtered
})

const sortedHoldings = computed(() => {
  const sorted = [...filteredHoldings.value]

  sorted.sort((a, b) => {
    let aVal: any
    let bVal: any

    switch (sortBy.value) {
      case 'stock_symbol':
        aVal = a.stock_symbol.toLowerCase()
        bVal = b.stock_symbol.toLowerCase()
        break
      case 'account_name':
        aVal = a.account_name.toLowerCase()
        bVal = b.account_name.toLowerCase()
        break
      case 'quantity':
        aVal = a.quantity
        bVal = b.quantity
        break
      case 'average_price':
        aVal = a.average_price
        bVal = b.average_price
        break
      case 'current_price':
        aVal = a.current_price || 0
        bVal = b.current_price || 0
        break
      case 'invested_value':
        aVal = a.invested_value
        bVal = b.invested_value
        break
      case 'current_value':
        aVal = a.current_value
        bVal = b.current_value
        break
      case 'gain_loss':
        aVal = a.gain_loss
        bVal = b.gain_loss
        break
      case 'gain_loss_percentage':
        aVal = a.gain_loss_percentage
        bVal = b.gain_loss_percentage
        break
      default:
        return 0
    }

    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return sorted
})

const setSortBy = (column: string) => {
  if (sortBy.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = column
    sortDirection.value = 'asc'
  }
}

onMounted(() => {
  loadAccounts()
  loadStocks()
  loadData()
})
</script>

<template>
  <div class="dashboard">
    <div class="header">
      <h1>Portfolio Dashboard</h1>
      <button @click="updateAllPrices" :disabled="updating" class="btn-primary">
        {{ updating ? 'Updating...' : 'Update Prices' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="summary" class="content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="card">
          <h3>Total Invested</h3>
          <p class="value">{{ formatCurrency(summary.total_invested) }}</p>
        </div>
        <div class="card">
          <h3>Current Value</h3>
          <p class="value">{{ formatCurrency(summary.total_current_value) }}</p>
        </div>
        <div class="card">
          <h3>Total Gain/Loss</h3>
          <p class="value" :class="getGainLossClass(summary.total_gain_loss)">
            {{ formatCurrency(summary.total_gain_loss) }}
            ({{ summary.total_gain_loss_percentage.toFixed(2) }}%)
          </p>
        </div>
        <div class="card">
          <h3>Holdings</h3>
          <p class="value">{{ summary.holdings_count }} across {{ summary.accounts_count }} accounts</p>
        </div>
      </div>

      <!-- Holdings Table -->
      <div class="holdings-section">
        <h2>Your Holdings</h2>

        <!-- Filter Section -->
        <div class="filter-section">
          <div class="filter-group">
            <label for="account-filter">Filter by Account:</label>
            <select id="account-filter" v-model.number="selectedAccountId">
              <option :value="null">All Accounts</option>
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="stock-filter">Filter by Stock:</label>
            <select id="stock-filter" v-model.number="selectedStockId">
              <option :value="null">All Stocks</option>
              <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
                {{ stock.symbol }} - {{ stock.name }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="holdings.length === 0" class="empty-state">
          <p>No holdings yet. Start by adding some stocks!</p>
          <router-link to="/holdings/add" class="btn-primary">Add Holding</router-link>
        </div>
        <table v-else class="holdings-table">
          <thead>
            <tr>
              <th @click="setSortBy('stock_symbol')" class="sortable">
                Stock
                <span class="sort-indicator" v-if="sortBy === 'stock_symbol'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('account_name')" class="sortable">
                Account
                <span class="sort-indicator" v-if="sortBy === 'account_name'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('quantity')" class="sortable">
                Quantity
                <span class="sort-indicator" v-if="sortBy === 'quantity'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('average_price')" class="sortable">
                Avg Price
                <span class="sort-indicator" v-if="sortBy === 'average_price'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('current_price')" class="sortable">
                Current Price
                <span class="sort-indicator" v-if="sortBy === 'current_price'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('invested_value')" class="sortable">
                Invested
                <span class="sort-indicator" v-if="sortBy === 'invested_value'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('current_value')" class="sortable">
                Current Value
                <span class="sort-indicator" v-if="sortBy === 'current_value'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
              <th @click="setSortBy('gain_loss')" class="sortable">
                Gain/Loss
                <span class="sort-indicator" v-if="sortBy === 'gain_loss'">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="holding in sortedHoldings" :key="holding.id">
              <td>
                <strong>{{ holding.stock_symbol }}</strong>
                <br />
                <small>{{ holding.stock_name }}</small>
              </td>
              <td>{{ holding.account_name }}</td>
              <td>{{ holding.quantity }}</td>
              <td>{{ formatCurrency(holding.average_price) }}</td>
              <td>{{ holding.current_price ? formatCurrency(holding.current_price) : 'N/A' }}</td>
              <td>{{ formatCurrency(holding.invested_value) }}</td>
              <td>{{ formatCurrency(holding.current_value) }}</td>
              <td :class="getGainLossClass(holding.gain_loss)">
                {{ formatCurrency(holding.gain_loss) }}
                <br />
                <small>({{ holding.gain_loss_percentage.toFixed(2) }}%)</small>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
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

.btn-primary:hover:not(:disabled) {
  background-color: #359268;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
  color: #666;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
}

.card .value {
  margin: 0;
  font-size: 1.8rem;
  font-weight: bold;
  color: #2c3e50;
}

.positive {
  color: #42b983;
}

.negative {
  color: #e74c3c;
}

.neutral {
  color: #666;
}

.holdings-section {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.holdings-section h2 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.filter-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.filter-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.filter-section label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.filter-section select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.empty-state p {
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.holdings-table {
  width: 100%;
  border-collapse: collapse;
}

.holdings-table th,
.holdings-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.holdings-table th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.holdings-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.holdings-table th.sortable:hover {
  background-color: #e8e8e8;
}

.sort-indicator {
  display: inline-block;
  margin-left: 0.5rem;
  font-size: 0.8rem;
  color: #42b983;
}

.holdings-table tbody tr:hover {
  background-color: #f9f9f9;
}

.holdings-table td strong {
  color: #2c3e50;
}

.holdings-table td small {
  color: #666;
  font-size: 0.85rem;
}
</style>
