<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { holdingApi, accountApi, stockApi } from '@/services/api'
import type { Account, Stock } from '@/types'

const router = useRouter()
const route = useRoute()

const isEditMode = ref(false)
const holdingId = ref<number | null>(null)
const formData = ref({
  account_id: null as number | null,
  stock_id: null as number | null,
  quantity: null as number | null,
  average_price: null as number | null,
  notes: ''
})
const accounts = ref<Account[]>([])
const stocks = ref<Stock[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const loadData = async () => {
  try {
    const [accountsRes, stocksRes] = await Promise.all([
      accountApi.getAll(),
      stockApi.getAll()
    ])
    accounts.value = accountsRes.data
    stocks.value = stocksRes.data
  } catch (err: any) {
    error.value = 'Failed to load accounts and stocks'
    console.error('Error loading data:', err)
  }
}

const loadHolding = async (id: number) => {
  loading.value = true
  try {
    const response = await holdingApi.getById(id)
    formData.value = {
      account_id: response.data.account_id,
      stock_id: response.data.stock_id,
      quantity: response.data.quantity,
      average_price: response.data.average_price,
      notes: response.data.notes || ''
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load holding'
    console.error('Error loading holding:', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formData.value.account_id || !formData.value.stock_id || !formData.value.quantity || !formData.value.average_price) {
    error.value = 'All fields except notes are required'
    return
  }

  loading.value = true
  error.value = null

  try {
    const payload = {
      account_id: formData.value.account_id,
      stock_id: formData.value.stock_id,
      quantity: formData.value.quantity,
      average_price: formData.value.average_price,
      notes: formData.value.notes || undefined
    }

    if (isEditMode.value && holdingId.value) {
      await holdingApi.update(holdingId.value, payload)
    } else {
      await holdingApi.create(payload)
    }
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to save holding'
    console.error('Error saving holding:', err)
  } finally {
    loading.value = false
  }
}

const cancel = () => {
  router.push('/')
}

onMounted(async () => {
  await loadData()

  if (route.params.id) {
    isEditMode.value = true
    holdingId.value = parseInt(route.params.id as string)
    await loadHolding(holdingId.value)
  }
})
</script>

<template>
  <div class="holding-form-page">
    <div class="form-container">
      <h1>{{ isEditMode ? 'Edit Holding' : 'Add Holding' }}</h1>

      <div v-if="error" class="error-message">{{ error }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="account">Account *</label>
          <select
            id="account"
            v-model.number="formData.account_id"
            required
            :disabled="loading || isEditMode"
          >
            <option :value="null">Select an account</option>
            <option v-for="account in accounts" :key="account.id" :value="account.id">
              {{ account.name }}
            </option>
          </select>
          <router-link v-if="accounts.length === 0" to="/accounts/add" class="add-link">
            No accounts found. Add one now →
          </router-link>
        </div>

        <div class="form-group">
          <label for="stock">Stock *</label>
          <select
            id="stock"
            v-model.number="formData.stock_id"
            required
            :disabled="loading || isEditMode"
          >
            <option :value="null">Select a stock</option>
            <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
              {{ stock.symbol }} - {{ stock.name }}
            </option>
          </select>
          <router-link v-if="stocks.length === 0" to="/stocks/add" class="add-link">
            No stocks found. Add one now →
          </router-link>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="quantity">Quantity *</label>
            <input
              id="quantity"
              v-model.number="formData.quantity"
              type="number"
              step="0.01"
              placeholder="e.g., 10"
              required
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label for="average_price">Average Price *</label>
            <input
              id="average_price"
              v-model.number="formData.average_price"
              type="number"
              step="0.01"
              placeholder="e.g., 150.00"
              required
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="notes">Notes</label>
          <textarea
            id="notes"
            v-model="formData.notes"
            placeholder="Optional notes about this holding"
            rows="3"
            :disabled="loading"
          ></textarea>
        </div>

        <div class="form-actions">
          <button type="button" @click="cancel" class="btn-secondary" :disabled="loading">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Saving...' : (isEditMode ? 'Update Holding' : 'Add Holding') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.holding-form-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.form-container {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h1 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
  font-size: 1.8rem;
}

.error-message {
  background-color: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #2c3e50;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #42b983;
}

.form-group input:disabled,
.form-group select:disabled,
.form-group textarea:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.add-link {
  display: inline-block;
  margin-top: 0.5rem;
  color: #42b983;
  font-size: 0.9rem;
  text-decoration: none;
}

.add-link:hover {
  text-decoration: underline;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
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

.btn-secondary {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #7f8c8d;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
