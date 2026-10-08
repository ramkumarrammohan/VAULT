<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mutualFundApi } from '@/services/api'
import type { MutualFundOverview } from '@/types'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const funds = ref<MutualFundOverview[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const refreshingFunds = ref<Set<number>>(new Set())

const loadFunds = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await mutualFundApi.getOverview()
    funds.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load mutual funds'
    console.error('Error loading mutual funds:', err)
  } finally {
    loading.value = false
  }
}

const deleteFund = async (id: number, name: string) => {
  if (!confirm(`Are you sure you want to delete fund "${name}"? This will also delete all its transactions.`)) {
    return
  }
  try {
    await mutualFundApi.delete(id)
    await loadFunds()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to delete mutual fund'
    console.error('Error deleting mutual fund:', err)
  }
}

const refreshNav = async (id: number, schemeCode?: string) => {
  if (!schemeCode) {
    alert('This fund has no AMFI scheme code, so its NAV cannot be auto-refreshed.')
    return
  }
  refreshingFunds.value.add(id)
  error.value = null
  try {
    await mutualFundApi.updateNav(schemeCode)
    await loadFunds()
  } catch (err: any) {
    const errorData = err.response?.data
    if (err.response?.status === 429) {
      alert(`Unable to refresh NAV for ${schemeCode}\n\n${errorData?.error || 'NAV provider is temporarily unavailable.'}\n\nYou can continue using the existing NAV shown in the table.`)
    } else {
      error.value = errorData?.hint ? `${errorData.error}\n${errorData.hint}` : (errorData?.error || `Failed to update NAV for ${schemeCode}`)
    }
    console.error('Error updating NAV:', err)
  } finally {
    refreshingFunds.value.delete(id)
  }
}

const isRefreshing = (id: number) => refreshingFunds.value.has(id)

const goToAdd = () => router.push('/mutual-funds/add')
const goToEdit = (id: number) => router.push(`/mutual-funds/edit/${id}`)

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'Never'
  const dateStr = dateString.endsWith('Z') ? dateString : dateString + 'Z'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return date.toLocaleDateString()
}

// Shorten AMC names, e.g. "HDFC Mutual Fund" -> "HDFC", "DSP Mutual Fund" -> "DSP"
const shortAmc = (amc?: string) => {
  if (!amc) return 'N/A'
  return amc.replace(/\s+Mutual\s+Fund$/i, '').trim() || amc
}

onMounted(() => {
  loadFunds()
})
</script>

<template>
  <div class="mutual-funds-page">
    <div class="header">
      <h1>Mutual Funds</h1>
      <div class="header-actions">
        <button @click="goToAdd" class="btn-primary">Add Fund</button>
      </div>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="funds.length === 0" class="empty-state">
      <p>No mutual funds yet. Add your first fund to get started!</p>
      <button @click="goToAdd" class="btn-primary">Add Fund</button>
    </div>

    <div v-else class="funds-table-container">
      <table class="funds-table">
        <thead>
          <tr>
            <th>Scheme</th>
            <th>AMC</th>
            <th>Category</th>
            <th>Current Price (NAV)</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fund in funds" :key="fund.id">
            <td>
              <strong>{{ fund.name }}</strong>
              <br />
              <small>{{ fund.scheme_code || 'No scheme code' }}</small>
            </td>
            <td>{{ shortAmc(fund.amc) }}</td>
            <td>{{ fund.category || 'N/A' }}</td>
            <td>{{ fund.nav ? formatCurrency(fund.nav, 'INR') : 'N/A' }}</td>
            <td>{{ formatDate(fund.nav_date) }}</td>
            <td class="actions">
              <button @click="refreshNav(fund.id, fund.scheme_code)" class="btn-refresh" :disabled="isRefreshing(fund.id)">
                {{ isRefreshing(fund.id) ? 'Updating...' : 'Refresh' }}
              </button>
              <button @click="goToEdit(fund.id)" class="btn-secondary">Edit</button>
              <button @click="deleteFund(fund.id, fund.name)" class="btn-danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.mutual-funds-page {
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

.header-actions {
  display: flex;
  gap: 0.75rem;
}

h1 {
  font-size: 2rem;
  color: var(--text-primary);
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
  font-size: 0.85rem;
  margin-right: 0.5rem;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #2980b9;
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
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.empty-state p {
  margin-bottom: 1rem;
}

.funds-table-container {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.funds-table {
  width: 100%;
  border-collapse: collapse;
}

.funds-table th,
.funds-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.funds-table th {
  background-color: var(--bg-tertiary);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
  text-transform: uppercase;
}

.funds-table tbody tr:hover {
  background-color: var(--table-hover);
}

.funds-table td strong {
  color: var(--text-primary);
}

.funds-table td small {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.funds-table td.actions {
  white-space: nowrap;
}
</style>
