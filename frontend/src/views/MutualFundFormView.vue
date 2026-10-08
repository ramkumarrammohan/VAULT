<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { mutualFundApi } from '@/services/api'

const router = useRouter()
const route = useRoute()

const isEditMode = ref(false)
const fundId = ref<number | null>(null)
const formData = ref({
  scheme_code: '',
  name: '',
  amc: '',
  category: '',
  plan: '',
  option: '',
  isin: '',
  folio: '',
  nav: null as number | null,
  nav_date: ''
})
const loading = ref(false)
const searching = ref(false)
const lookingUp = ref(false)
const error = ref<string | null>(null)

// Scheme search state
const searchQuery = ref('')
const searchResults = ref<{ scheme_code: string; scheme_name: string }[]>([])
const showSearchResults = ref(false)

const searchSchemes = async () => {
  if (!searchQuery.value.trim()) {
    error.value = 'Enter a keyword to search schemes (e.g., "HDFC Mid Cap")'
    return
  }
  searching.value = true
  error.value = null
  try {
    const response = await mutualFundApi.searchSchemes(searchQuery.value.trim())
    searchResults.value = response.data.results || []
    showSearchResults.value = true
    if (searchResults.value.length === 0) {
      error.value = 'No schemes found. Try a different keyword.'
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to search schemes'
    console.error('Error searching schemes:', err)
  } finally {
    searching.value = false
  }
}

const selectScheme = async (scheme: { scheme_code: string; scheme_name: string }) => {
  showSearchResults.value = false
  formData.value.scheme_code = scheme.scheme_code
  formData.value.name = scheme.scheme_name
  // Fetch metadata + latest NAV to auto-fill
  lookingUp.value = true
  error.value = null
  try {
    const response = await mutualFundApi.getScheme(scheme.scheme_code)
    const data = response.data
    if (data.amc) formData.value.amc = data.amc
    if (data.category) formData.value.category = data.category
    if (data.plan) formData.value.plan = data.plan
    if (data.option) formData.value.option = data.option
    if (data.nav) formData.value.nav = data.nav
    if (data.nav_date) formData.value.nav_date = data.nav_date
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch scheme details'
    console.error('Error fetching scheme:', err)
  } finally {
    lookingUp.value = false
  }
}

const lookupByCode = async () => {
  if (!formData.value.scheme_code.trim()) {
    error.value = 'Enter an AMFI scheme code'
    return
  }
  lookingUp.value = true
  error.value = null
  try {
    const response = await mutualFundApi.getScheme(formData.value.scheme_code.trim())
    const data = response.data
    formData.value.name = data.scheme_name || formData.value.name
    if (data.amc) formData.value.amc = data.amc
    if (data.category) formData.value.category = data.category
    if (data.plan) formData.value.plan = data.plan
    if (data.option) formData.value.option = data.option
    if (data.nav) formData.value.nav = data.nav
    if (data.nav_date) formData.value.nav_date = data.nav_date
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch scheme details'
    console.error('Error fetching scheme:', err)
  } finally {
    lookingUp.value = false
  }
}

const loadFund = async (id: number) => {
  loading.value = true
  try {
    const response = await mutualFundApi.getById(id)
    const data = response.data
    formData.value = {
      scheme_code: data.scheme_code || '',
      name: data.name,
      amc: data.amc || '',
      category: data.category || '',
      plan: data.plan || '',
      option: data.option || '',
      isin: data.isin || '',
      folio: data.folio || '',
      nav: data.nav ?? null,
      nav_date: data.nav_date ? data.nav_date.slice(0, 10) : ''
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load mutual fund'
    console.error('Error loading mutual fund:', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    error.value = 'Fund name is required'
    return
  }
  loading.value = true
  error.value = null

  const payload: any = {
    scheme_code: formData.value.scheme_code.trim() || undefined,
    name: formData.value.name.trim(),
    amc: formData.value.amc.trim() || undefined,
    category: formData.value.category.trim() || undefined,
    plan: formData.value.plan.trim() || undefined,
    option: formData.value.option.trim() || undefined,
    isin: formData.value.isin.trim() || undefined,
    folio: formData.value.folio.trim() || undefined,
    nav: formData.value.nav ?? undefined,
    nav_date: formData.value.nav_date || undefined
  }

  try {
    if (isEditMode.value && fundId.value) {
      await mutualFundApi.update(fundId.value, payload)
    } else {
      await mutualFundApi.create(payload)
    }
    router.push('/mutual-funds')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to save mutual fund'
    console.error('Error saving mutual fund:', err)
  } finally {
    loading.value = false
  }
}

const cancel = () => router.push('/mutual-funds')

onMounted(() => {
  if (route.params.id) {
    isEditMode.value = true
    fundId.value = parseInt(route.params.id as string)
    loadFund(fundId.value)
  }
})
</script>

<template>
  <div class="fund-form-page">
    <div class="form-container">
      <h1>{{ isEditMode ? 'Edit Mutual Fund' : 'Add Mutual Fund' }}</h1>

      <div v-if="error" class="error-message">{{ error }}</div>

      <!-- Scheme search (add mode only) -->
      <div v-if="!isEditMode" class="search-section">
        <label for="scheme-search">Search AMFI scheme</label>
        <div class="search-row">
          <input
            id="scheme-search"
            v-model="searchQuery"
            type="text"
            placeholder="e.g., HDFC Mid Cap, Nippon Small Cap"
            @keyup.enter="searchSchemes"
          />
          <button type="button" @click="searchSchemes" class="btn-lookup" :disabled="searching">
            {{ searching ? 'Searching...' : 'Search' }}
          </button>
        </div>
        <div v-if="showSearchResults && searchResults.length > 0" class="search-results">
          <div
            v-for="scheme in searchResults"
            :key="scheme.scheme_code"
            class="search-result-item"
            @click="selectScheme(scheme)"
          >
            <strong>{{ scheme.scheme_name }}</strong>
            <small>{{ scheme.scheme_code }}</small>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label for="scheme_code">AMFI Scheme Code</label>
            <div class="code-input">
              <input
                id="scheme_code"
                v-model="formData.scheme_code"
                type="text"
                placeholder="e.g., 119598"
                :disabled="loading"
              />
              <button
                v-if="!isEditMode"
                type="button"
                @click="lookupByCode"
                class="btn-lookup"
                :disabled="lookingUp || !formData.scheme_code.trim()"
              >
                {{ lookingUp ? 'Fetching...' : 'Fetch' }}
              </button>
            </div>
            <small class="hint">Optional but enables automatic NAV refresh.</small>
          </div>

          <div class="form-group">
            <label for="name">Fund Name *</label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              placeholder="e.g., HDFC Mid-Cap Opportunities Fund - Direct - Growth"
              required
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="amc">AMC</label>
            <input id="amc" v-model="formData.amc" type="text" placeholder="e.g., HDFC Mutual Fund" :disabled="loading" />
          </div>
          <div class="form-group">
            <label for="category">Category</label>
            <input id="category" v-model="formData.category" type="text" placeholder="e.g., Equity: Mid Cap" :disabled="loading" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="plan">Plan</label>
            <select id="plan" v-model="formData.plan" :disabled="loading">
              <option value="">Select plan</option>
              <option value="DIRECT">Direct</option>
              <option value="REGULAR">Regular</option>
            </select>
          </div>
          <div class="form-group">
            <label for="option">Option</label>
            <select id="option" v-model="formData.option" :disabled="loading">
              <option value="">Select option</option>
              <option value="GROWTH">Growth</option>
              <option value="IDCW">IDCW (Dividend)</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="isin">ISIN</label>
            <input id="isin" v-model="formData.isin" type="text" placeholder="e.g., INE00A0D0HN2" :disabled="loading" />
          </div>
          <div class="form-group">
            <label for="folio">Folio / Platform</label>
            <input id="folio" v-model="formData.folio" type="text" placeholder="Optional folio number" :disabled="loading" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="nav">Latest NAV</label>
            <input id="nav" v-model.number="formData.nav" type="number" step="0.0001" placeholder="e.g., 245.6789" :disabled="loading" />
            <small class="hint">Optional - can be updated later via "Update NAV".</small>
          </div>
          <div class="form-group">
            <label for="nav_date">NAV Date</label>
            <input id="nav_date" v-model="formData.nav_date" type="date" :disabled="loading" />
          </div>
        </div>

        <div class="form-actions">
          <button type="button" @click="cancel" class="btn-secondary" :disabled="loading">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Saving...' : (isEditMode ? 'Update Fund' : 'Add Fund') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.fund-form-page {
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

.search-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.search-section label {
  display: block;
  margin-bottom: 0.5rem;
  color: #2c3e50;
  font-weight: 500;
}

.search-row {
  display: flex;
  gap: 0.5rem;
}

.search-row input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.search-results {
  margin-top: 0.75rem;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.search-result-item {
  padding: 0.6rem 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.search-result-item:hover {
  background-color: #f0f7f4;
}

.search-result-item small {
  color: #666;
  white-space: nowrap;
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
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #42b983;
}

.form-group input:disabled,
.form-group select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.code-input {
  display: flex;
  gap: 0.5rem;
}

.code-input input {
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
</style>
