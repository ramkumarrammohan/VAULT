<script setup lang="ts">

import { ref, computed, onMounted } from 'vue'
import { portfolioApi, priceApi, accountApi, stockApi } from '@/services/api'
import type { PortfolioSummary, Holding, Account, Stock, ConsolidatedHolding } from '@/types'
import { formatCurrency } from '@/utils/currency'
import HoldingsTable from '@/components/HoldingsTable.vue'


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
const expandedStocks = ref<Set<number>>(new Set())

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

const getGainLossClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const toggleExpand = (stockId: number) => {
  const next = new Set(expandedStocks.value)
  if (next.has(stockId)) {
    next.delete(stockId)
  } else {
    next.add(stockId)
  }
  expandedStocks.value = next
}

// Build consolidated holdings map grouped by currency
const consolidatedHoldings = computed<ConsolidatedHolding[]>(() => {
  let filtered = holdings.value

  if (selectedAccountId.value) {
    filtered = filtered.filter(h => h.account_id === selectedAccountId.value)
  }

  if (selectedStockId.value) {
    filtered = filtered.filter(h => h.stock_id === selectedStockId.value)
  }

  const map = new Map<number, ConsolidatedHolding>()

  for (const h of filtered) {
    if (!map.has(h.stock_id)) {
      map.set(h.stock_id, {
        stock_id: h.stock_id,
        stock_symbol: h.stock_symbol,
        stock_name: h.stock_name,
        currency: h.currency,
        current_price: h.current_price,
        quantity: 0,
        average_price: 0,
        invested_value: 0,
        current_value: 0,
        gain_loss: 0,
        gain_loss_percentage: 0,
        sub_holdings: []
      })
    }
    const entry = map.get(h.stock_id)!
    entry.quantity += h.quantity
    entry.invested_value += h.invested_value
    entry.current_value += h.current_value
    entry.gain_loss += h.gain_loss
    entry.sub_holdings.push(h)
  }

  for (const entry of map.values()) {
    entry.average_price = entry.quantity > 0 ? entry.invested_value / entry.quantity : 0
    entry.gain_loss_percentage = entry.invested_value > 0 ? (entry.gain_loss / entry.invested_value) * 100 : 0
  }

  return Array.from(map.values())
})

// Split consolidated holdings by currency
const inrHoldings = computed(() =>
  consolidatedHoldings.value.filter(h => (h.currency ?? 'INR') === 'INR')
)
const usdHoldings = computed(() =>
  consolidatedHoldings.value.filter(h => h.currency === 'USD')
)
const otherHoldings = computed(() =>
  consolidatedHoldings.value.filter(h => h.currency && h.currency !== 'INR' && h.currency !== 'USD')
)

const sortHoldings = (list: ConsolidatedHolding[]) => {
  const sorted = [...list]
  sorted.sort((a, b) => {
    let aVal: any
    let bVal: any

    switch (sortBy.value) {
      case 'stock_symbol':
        aVal = a.stock_symbol.toLowerCase()
        bVal = b.stock_symbol.toLowerCase()
        break
      case 'quantity':
        aVal = a.quantity; bVal = b.quantity; break
      case 'average_price':
        aVal = a.average_price; bVal = b.average_price; break
      case 'current_price':
        aVal = a.current_price || 0; bVal = b.current_price || 0; break
      case 'invested_value':
        aVal = a.invested_value; bVal = b.invested_value; break
      case 'current_value':
        aVal = a.current_value; bVal = b.current_value; break
      case 'gain_loss':
        aVal = a.gain_loss; bVal = b.gain_loss; break
      case 'gain_loss_percentage':
        aVal = a.gain_loss_percentage; bVal = b.gain_loss_percentage; break
      default:
        return 0
    }

    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })
  return sorted
}

const sortedInrHoldings = computed(() => sortHoldings(inrHoldings.value))
const sortedUsdHoldings = computed(() => sortHoldings(usdHoldings.value))
const sortedOtherHoldings = computed(() => sortHoldings(otherHoldings.value))

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
      <div style="display: flex; gap: 1rem; align-items: center;">
        <button @click="updateAllPrices" :disabled="updating" class="btn-primary">
          {{ updating ? 'Updating...' : 'Update Prices' }}
        </button>
        <router-link to="/corporate-events" class="btn-primary">Corporate Actions</router-link>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="summary" class="content">

      <!-- Overview counts -->
      <div class="summary-cards">
        <div class="card">
          <h3>Holdings</h3>
          <p class="value">{{ summary.holdings_count }} across {{ summary.accounts_count }} accounts</p>
        </div>
        <div v-for="(cur, code) in summary.by_currency" :key="code" class="card currency-card">
          <h3>{{ code === 'INR' ? '🇮🇳' : code === 'USD' ? '🇺🇸' : '🌐' }} {{ code }} Portfolio</h3>
          <p class="value">{{ formatCurrency(cur.total_current_value, code) }}</p>
          <p class="sub-value" :class="getGainLossClass(cur.total_gain_loss)">
            {{ formatCurrency(cur.total_gain_loss, code) }}
            ({{ cur.total_gain_loss_percentage.toFixed(2) }}%)
          </p>
          <p class="sub-label">Invested: {{ formatCurrency(cur.total_invested, code) }}</p>
        </div>
      </div>

      <!-- Filter bar (shared) -->
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
        <p>No holdings yet. Add transactions to see your portfolio.</p>
        <router-link to="/transactions" class="btn-primary">Add Transaction</router-link>
      </div>

      <template v-else>
        <!-- INR section -->
        <div v-if="sortedInrHoldings.length > 0" class="holdings-section">
          <h2>🇮🇳 Indian Portfolio <span class="currency-badge">INR</span></h2>
          <HoldingsTable
            :holdings="sortedInrHoldings"
            currency="INR"
            :sort-by="sortBy"
            :sort-direction="sortDirection"
            :expanded-stocks="expandedStocks"
            @sort="setSortBy"
            @toggle-expand="toggleExpand"
            :get-gain-loss-class="getGainLossClass"
          />
        </div>

        <!-- USD section -->
        <div v-if="sortedUsdHoldings.length > 0" class="holdings-section">
          <h2>🇺🇸 US Portfolio <span class="currency-badge">USD</span></h2>
          <HoldingsTable
            :holdings="sortedUsdHoldings"
            currency="USD"
            :sort-by="sortBy"
            :sort-direction="sortDirection"
            :expanded-stocks="expandedStocks"
            @sort="setSortBy"
            @toggle-expand="toggleExpand"
            :get-gain-loss-class="getGainLossClass"
          />
        </div>

        <!-- Other currencies -->
        <div v-if="sortedOtherHoldings.length > 0" class="holdings-section">
          <h2>🌐 Other Holdings</h2>
          <HoldingsTable
            :holdings="sortedOtherHoldings"
            :currency="sortedOtherHoldings[0]?.currency ?? 'USD'"
            :sort-by="sortBy"
            :sort-direction="sortDirection"
            :expanded-stocks="expandedStocks"
            @sort="setSortBy"
            @toggle-expand="toggleExpand"
            :get-gain-loss-class="getGainLossClass"
          />
        </div>
      </template>
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

.currency-card .sub-value {
  margin: 0.25rem 0 0;
  font-size: 1rem;
  font-weight: 600;
}

.currency-card .sub-label {
  margin: 0.2rem 0 0;
  font-size: 0.85rem;
  color: #888;
}

.currency-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  background: #42b983;
  color: white;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  vertical-align: middle;
  margin-left: 0.4rem;
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

.consolidated-row {
  cursor: pointer;
}

.consolidated-row:hover {
  background-color: #f0f7f4 !important;
}

.consolidated-row.expanded {
  background-color: #e8f5ee;
}

.expand-chevron {
  display: inline-block;
  margin-right: 0.5rem;
  font-size: 0.75rem;
  color: #42b983;
  transition: transform 0.2s;
}

.sub-row {
  background-color: #fafafa;
}

.sub-row:hover {
  background-color: #f0f0f0 !important;
}

.sub-row td {
  font-size: 0.9rem;
  color: #555;
  border-bottom: 1px solid #efefef;
}

.sub-account-cell {
  padding-left: 1.5rem !important;
}

.sub-indent {
  color: #42b983;
  margin-right: 0.4rem;
}

.holdings-table td strong {
  color: #2c3e50;
}

.holdings-table td small {
  color: #666;
  font-size: 0.85rem;
}
</style>
