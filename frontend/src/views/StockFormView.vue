<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { stockApi } from '@/services/api'

const router = useRouter()
const route = useRoute()

const isEditMode = ref(false)
const stockId = ref<number | null>(null)
const formData = ref({
  symbol: '',
  name: '',
  exchange: '',
  sector: '',
  current_price: null as number | null
})
const loading = ref(false)
const lookingUp = ref(false)
const error = ref<string | null>(null)

const loadStock = async (id: number) => {
  loading.value = true
  try {
    const response = await stockApi.getById(id)
    formData.value = {
      symbol: response.data.symbol,
      name: response.data.name,
      exchange: response.data.exchange || '',
      sector: response.data.sector || '',
      current_price: response.data.current_price
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load stock'
    console.error('Error loading stock:', err)
  } finally {
    loading.value = false
  }
}

const lookupStock = async () => {
  if (!formData.value.symbol.trim()) {
    error.value = 'Please enter a stock symbol'
    return
  }

  lookingUp.value = true
  error.value = null

  try {
    const response = await stockApi.fetchInfo(formData.value.symbol)
    const data = response.data

    if (data.name) {
      formData.value.name = data.name
    }
    if (data.exchange) {
      formData.value.exchange = data.exchange
    }
    if (data.sector) {
      formData.value.sector = data.sector
    }
    if (data.current_price) {
      formData.value.current_price = data.current_price
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch stock information'
    console.error('Error looking up stock:', err)
  } finally {
    lookingUp.value = false
  }
}

const handleSubmit = async () => {
  if (!formData.value.symbol.trim() || !formData.value.name.trim()) {
    error.value = 'Symbol and name are required'
    return
  }

  loading.value = true
  error.value = null

  try {
    const payload = {
      symbol: formData.value.symbol.toUpperCase(),
      name: formData.value.name,
      exchange: formData.value.exchange || undefined,
      sector: formData.value.sector || undefined,
      current_price: formData.value.current_price || undefined
    }

    if (isEditMode.value && stockId.value) {
      await stockApi.update(stockId.value, payload)
    } else {
      await stockApi.create(payload)
    }
    router.push('/stocks')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to save stock'
    console.error('Error saving stock:', err)
  } finally {
    loading.value = false
  }
}

const cancel = () => {
  router.push('/stocks')
}

onMounted(() => {
  if (route.params.id) {
    isEditMode.value = true
    stockId.value = parseInt(route.params.id as string)
    loadStock(stockId.value)
  }
})
</script>

<template>
  <div class="stock-form-page">
    <div class="form-container">
      <h1>{{ isEditMode ? 'Edit Stock' : 'Add Stock' }}</h1>

      <div v-if="error" class="error-message">{{ error }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label for="symbol">Stock Symbol *</label>
            <div class="symbol-input">
              <input
                id="symbol"
                v-model="formData.symbol"
                type="text"
                placeholder="e.g., AAPL, RELIANCE.NS"
                required
                :disabled="loading || isEditMode"
              />
              <button
                v-if="!isEditMode"
                type="button"
                @click="lookupStock"
                class="btn-lookup"
                :disabled="lookingUp || !formData.symbol.trim()"
              >
                {{ lookingUp ? 'Looking up...' : 'Lookup' }}
              </button>
            </div>
            <small class="hint">Use .NS for NSE (India), .BO for BSE, plain symbol for US stocks</small>
          </div>

          <div class="form-group">
            <label for="name">Stock Name *</label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              placeholder="e.g., Apple Inc."
              required
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="exchange">Exchange</label>
            <input
              id="exchange"
              v-model="formData.exchange"
              type="text"
              placeholder="e.g., NASDAQ, NSE"
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label for="sector">Sector</label>
            <input
              id="sector"
              v-model="formData.sector"
              type="text"
              placeholder="e.g., Technology, Banking"
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="current_price">Current Price</label>
          <input
            id="current_price"
            v-model.number="formData.current_price"
            type="number"
            step="0.01"
            placeholder="e.g., 178.50"
            :disabled="loading"
          />
          <small class="hint">Optional - can be updated later via "Update Prices"</small>
        </div>

        <div class="form-actions">
          <button type="button" @click="cancel" class="btn-secondary" :disabled="loading">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Saving...' : (isEditMode ? 'Update Stock' : 'Add Stock') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.stock-form-page {
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

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #42b983;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.symbol-input {
  display: flex;
  gap: 0.5rem;
}

.symbol-input input {
  flex: 1;
}

.btn-lookup {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  white-space: nowrap;
  transition: background-color 0.3s;
}

.btn-lookup:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-lookup:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.hint {
  display: block;
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.85rem;
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
