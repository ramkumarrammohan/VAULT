<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { portfolioApi, holdingApi, priceApi } from '@/services/api'
import type { PortfolioSummary, Holding } from '@/types'

const summary = ref<PortfolioSummary | null>(null)
const holdings = ref<Holding[]>([])
const loading = ref(false)
const updating = ref(false)

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
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(value)
}

const getGainLossClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

onMounted(() => {
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
        <div v-if="holdings.length === 0" class="empty-state">
          <p>No holdings yet. Start by adding some stocks!</p>
          <router-link to="/holdings/add" class="btn-primary">Add Holding</router-link>
        </div>
        <table v-else class="holdings-table">
          <thead>
            <tr>
              <th>Stock</th>
              <th>Account</th>
              <th>Quantity</th>
              <th>Avg Price</th>
              <th>Current Price</th>
              <th>Invested</th>
              <th>Current Value</th>
              <th>Gain/Loss</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="holding in holdings" :key="holding.id">
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
