<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { accountApi, portfolioApi } from '@/services/api'
import type { Account, AccountSummary, CurrencyAccountSummary } from '@/types'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const accounts = ref<Account[]>([])
const summaries = ref<AccountSummary[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const loadAccounts = async () => {
  loading.value = true
  error.value = null
  try {
    const [accountsRes, summariesRes] = await Promise.all([
      accountApi.getAll(),
      portfolioApi.getByAccount()
    ])
    accounts.value = accountsRes.data
    summaries.value = summariesRes.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load accounts'
    console.error('Error loading accounts:', err)
  } finally {
    loading.value = false
  }
}

const summaryFor = (accountId: number): AccountSummary | undefined => {
  return summaries.value.find(s => s.account_id === accountId)
}

// Return the currency buckets to display. Falls back to a single bucket built
// from the top-level totals when the backend hasn't returned by_currency yet.
const currencyBucketsFor = (accountId: number): CurrencyAccountSummary[] => {
  const summary = summaryFor(accountId)
  if (!summary) return []
  if (summary.by_currency && summary.by_currency.length > 0) {
    return summary.by_currency
  }
  // Fallback: single bucket from top-level totals (INR default)
  return [{
    currency: 'INR',
    total_invested: summary.total_invested,
    total_current_value: summary.total_current_value,
    total_gain_loss: summary.total_gain_loss,
    total_gain_loss_percentage: summary.total_gain_loss_percentage,
    holdings_count: summary.holdings_count,
  }]
}

const hasSummary = (accountId: number): boolean => {
  return currencyBucketsFor(accountId).length > 0
}

const getGainLossClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const deleteAccount = async (id: number, name: string) => {
  if (!confirm(`Are you sure you want to delete account "${name}"? This will also delete all associated holdings.`)) {
    return
  }

  try {
    await accountApi.delete(id)
    await loadAccounts()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to delete account'
    console.error('Error deleting account:', err)
  }
}

const goToAdd = () => {
  router.push('/accounts/add')
}

const goToEdit = (id: number) => {
  router.push(`/accounts/edit/${id}`)
}

onMounted(() => {
  loadAccounts()
})
</script>

<template>
  <div class="accounts-page">
    <div class="header">
      <h1>Manage Accounts</h1>
      <button @click="goToAdd" class="btn-primary">Add Account</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="accounts.length === 0" class="empty-state">
      <p>No accounts yet. Add your first account to get started!</p>
    </div>

    <div v-else class="accounts-grid">
      <div v-for="account in accounts" :key="account.id" class="account-card">
        <div class="account-info">
          <h3>{{ account.name }}</h3>
          <p v-if="account.description" class="description">{{ account.description }}</p>
        </div>
        <div v-if="hasSummary(account.id)" class="account-summary">
          <div v-for="bucket in currencyBucketsFor(account.id)" :key="bucket.currency" class="currency-block">
            <div class="currency-header">
              <span class="currency-flag">{{ bucket.currency === 'INR' ? '🇮🇳' : bucket.currency === 'USD' ? '🇺🇸' : '🌐' }}</span>
              <span class="currency-code">{{ bucket.currency }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Invested</span>
              <span class="summary-value">{{ formatCurrency(bucket.total_invested, bucket.currency) }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Current Value</span>
              <span class="summary-value">{{ formatCurrency(bucket.total_current_value, bucket.currency) }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Gain/Loss</span>
              <span class="summary-value" :class="getGainLossClass(bucket.total_gain_loss)">
                {{ formatCurrency(bucket.total_gain_loss, bucket.currency) }}
                ({{ bucket.total_gain_loss_percentage.toFixed(2) }}%)
              </span>
            </div>
            <div class="summary-row">
              <span class="summary-label">Holdings</span>
              <span class="summary-value">{{ bucket.holdings_count }}</span>
            </div>
          </div>
        </div>
        <div v-else class="account-summary empty-summary">
          <span class="summary-label">No holdings yet</span>
        </div>
        <div class="account-actions">
          <button @click="goToEdit(account.id)" class="btn-secondary">Edit</button>
          <button @click="deleteAccount(account.id, account.name)" class="btn-danger">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.accounts-page {
  max-width: 1200px;
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

.btn-secondary {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
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
  font-size: 0.9rem;
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
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.account-card {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.account-info h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1.3rem;
}

.account-info .description {
  color: var(--text-secondary);
  margin: 0;
  font-size: 0.9rem;
}

.account-summary {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.account-summary.empty-summary {
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: center;
}

.currency-block + .currency-block {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--border-color);
}

.currency-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.25rem;
}

.currency-flag {
  font-size: 1rem;
}

.currency-code {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.85rem;
  text-transform: uppercase;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
}

.summary-row + .summary-row {
  border-top: 1px solid var(--border-light);
}

.summary-label {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.summary-value {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.positive { color: #42b983; }
.negative { color: #e74c3c; }
.neutral  { color: #666; }

.account-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}
</style>
