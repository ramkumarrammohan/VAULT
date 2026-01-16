<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { transactionApi, accountApi, stockApi } from '@/services/api'
import type { Transaction, Account, Stock } from '@/types'

const router = useRouter()
const transactions = ref<Transaction[]>([])
const accounts = ref<Account[]>([])
const stocks = ref<Stock[]>([])
const selectedAccountId = ref<number | null>(null)
const selectedStockId = ref<number | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const showAddModal = ref(false)
const showBulkUploadModal = ref(false)
const csvFile = ref<File | null>(null)
const csvData = ref<any[]>([])
const csvErrors = ref<string[]>([])
const uploadLoading = ref(false)

const formData = ref({
  account_id: null as number | null,
  stock_id: null as number | null,
  transaction_type: 'BUY' as 'BUY' | 'SELL',
  quantity: null as number | null,
  price: null as number | null,
  transaction_date: new Date().toISOString().slice(0, 16),
  fees: 0,
  notes: ''
})

const loadAccounts = async () => {
  try {
    const response = await accountApi.getAll()
    accounts.value = response.data
  } catch (err: any) {
    error.value = 'Failed to load accounts'
    console.error('Error loading accounts:', err)
  }
}

const loadStocks = async () => {
  try {
    const response = await stockApi.getAll()
    stocks.value = response.data
  } catch (err: any) {
    error.value = 'Failed to load stocks'
    console.error('Error loading stocks:', err)
  }
}

const loadTransactions = async () => {
  loading.value = true
  error.value = null
  try {
    const params: any = {}
    if (selectedAccountId.value) params.account_id = selectedAccountId.value
    if (selectedStockId.value) params.stock_id = selectedStockId.value

    const response = await transactionApi.getAll(params)
    transactions.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load transactions'
    console.error('Error loading transactions:', err)
  } finally {
    loading.value = false
  }
}

const deleteTransaction = async (id: number) => {
  if (!confirm('Are you sure you want to delete this transaction? This will reverse its effect on the holding.')) {
    return
  }

  try {
    await transactionApi.delete(id)
    await loadTransactions()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to delete transaction'
    console.error('Error deleting transaction:', err)
  }
}

const openAddModal = () => {
  formData.value = {
    account_id: null,
    stock_id: null,
    transaction_type: 'BUY',
    quantity: null,
    price: null,
    transaction_date: new Date().toISOString().slice(0, 16),
    fees: 0,
    notes: ''
  }
  showAddModal.value = true
}

const submitTransaction = async () => {
  if (!formData.value.account_id || !formData.value.stock_id || !formData.value.quantity || !formData.value.price) {
    error.value = 'Please fill all required fields'
    return
  }

  loading.value = true
  error.value = null

  try {
    await transactionApi.create({
      account_id: formData.value.account_id,
      stock_id: formData.value.stock_id,
      transaction_type: formData.value.transaction_type,
      quantity: formData.value.quantity,
      price: formData.value.price,
      transaction_date: formData.value.transaction_date,
      fees: formData.value.fees || 0,
      notes: formData.value.notes || undefined
    })
    showAddModal.value = false
    await loadTransactions()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to create transaction'
    console.error('Error creating transaction:', err)
  } finally {
    loading.value = false
  }
}

const submitAndReset = async () => {
  if (!formData.value.account_id || !formData.value.stock_id || !formData.value.quantity || !formData.value.price) {
    error.value = 'Please fill all required fields'
    return
  }

  loading.value = true
  error.value = null

  try {
    await transactionApi.create({
      account_id: formData.value.account_id,
      stock_id: formData.value.stock_id,
      transaction_type: formData.value.transaction_type,
      quantity: formData.value.quantity,
      price: formData.value.price,
      transaction_date: formData.value.transaction_date,
      fees: formData.value.fees || 0,
      notes: formData.value.notes || undefined
    })

    // Reset form but keep account and stock selections
    const currentAccountId = formData.value.account_id
    const currentStockId = formData.value.stock_id
    formData.value = {
      account_id: currentAccountId,
      stock_id: currentStockId,
      transaction_type: formData.value.transaction_type,
      quantity: null,
      price: null,
      transaction_date: new Date().toISOString().slice(0, 16),
      fees: 0,
      notes: ''
    }

    await loadTransactions()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to create transaction'
    console.error('Error creating transaction:', err)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2
  }).format(value)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const openBulkUploadModal = () => {
  csvFile.value = null
  csvData.value = []
  csvErrors.value = []
  showBulkUploadModal.value = true
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    if (!file.name.endsWith('.csv')) {
      csvErrors.value = ['Please select a CSV file']
      return
    }
    csvFile.value = file
    parseCSV(file)
  }
}

const parseCSV = (file: File) => {
  const reader = new FileReader()

  reader.onload = (e) => {
    try {
      const text = e.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())

      if (lines.length < 2) {
        csvErrors.value = ['CSV file must contain header and at least one data row']
        return
      }

      // Parse header
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())

      // Validate required columns
      const requiredColumns = ['account', 'stock_symbol', 'transaction_type', 'quantity', 'price', 'transaction_date']
      const missingColumns = requiredColumns.filter(col => !headers.includes(col))

      if (missingColumns.length > 0) {
        csvErrors.value = [`Missing required columns: ${missingColumns.join(', ')}`]
        return
      }

      // Parse data rows
      const parsed: any[] = []
      const errors: string[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim())
        const row: any = {}

        headers.forEach((header, index) => {
          row[header] = values[index] || ''
        })

        // Find account by name
        const account = accounts.value.find(a => a.name.toLowerCase() === row.account.toLowerCase())
        if (!account) {
          errors.push(`Row ${i}: Account "${row.account}" not found`)
          continue
        }

        // Find stock by symbol
        const stock = stocks.value.find(s => s.symbol.toUpperCase() === row.stock_symbol.toUpperCase())
        if (!stock) {
          errors.push(`Row ${i}: Stock "${row.stock_symbol}" not found`)
          continue
        }

        // Validate transaction type
        const transType = row.transaction_type.toUpperCase()
        if (transType !== 'BUY' && transType !== 'SELL') {
          errors.push(`Row ${i}: Invalid transaction type "${row.transaction_type}"`)
          continue
        }

        parsed.push({
          account_id: account.id,
          account_name: account.name,
          stock_id: stock.id,
          stock_symbol: stock.symbol,
          transaction_type: transType,
          quantity: parseFloat(row.quantity),
          price: parseFloat(row.price),
          fees: row.fees ? parseFloat(row.fees) : 0,
          transaction_date: row.transaction_date,
          notes: row.notes || ''
        })
      }

      csvData.value = parsed
      csvErrors.value = errors

    } catch (err: any) {
      csvErrors.value = ['Failed to parse CSV file: ' + err.message]
    }
  }

  reader.onerror = () => {
    csvErrors.value = ['Failed to read file']
  }

  reader.readAsText(file)
}

const submitBulkTransactions = async () => {
  if (csvData.value.length === 0) {
    error.value = 'No valid transactions to upload'
    return
  }

  uploadLoading.value = true
  error.value = null

  try {
    console.log('Sending bulk transactions:', csvData.value)
    const response = await transactionApi.createBulk({
      transactions: csvData.value
    })

    showBulkUploadModal.value = false
    await loadTransactions()

    // Show success message
    const successMsg = `Successfully uploaded ${response.data.success_count} transactions`
    const errorMsg = response.data.error_count > 0 ? `, ${response.data.error_count} failed` : ''
    alert(successMsg + errorMsg)

  } catch (err: any) {
    console.error('Error uploading transactions:', err)
    console.error('Error response:', err.response?.data)
    error.value = err.response?.data?.error || 'Failed to upload transactions'
  } finally {
    uploadLoading.value = false
  }
}

const downloadTemplate = () => {
  const template = 'account,stock_symbol,transaction_type,quantity,price,transaction_date,fees,notes\nMy Account,AAPL,BUY,10,150.50,2024-01-15,5.00,Sample transaction'
  const blob = new Blob([template], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transactions_template.csv'
  a.click()
  window.URL.revokeObjectURL(url)
}

onMounted(async () => {
  await loadAccounts()
  await loadStocks()
  await loadTransactions()
})
</script>

<template>
  <div class="transactions-page">
    <div class="header">
      <h1>Transaction History</h1>
      <div class="header-actions">
        <button @click="openBulkUploadModal" class="btn-secondary">Bulk Upload (CSV)</button>
        <button @click="openAddModal" class="btn-primary">Add Transaction</button>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-group">
        <label for="account-filter">Filter by Account:</label>
        <select id="account-filter" v-model.number="selectedAccountId" @change="loadTransactions">
          <option :value="null">All Accounts</option>
          <option v-for="account in accounts" :key="account.id" :value="account.id">
            {{ account.name }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label for="stock-filter">Filter by Stock:</label>
        <select id="stock-filter" v-model.number="selectedStockId" @change="loadTransactions">
          <option :value="null">All Stocks</option>
          <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
            {{ stock.symbol }} - {{ stock.name }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="transactions.length === 0" class="empty-state">
      <p>No transactions yet. Add your first transaction to track your trades!</p>
    </div>

    <div v-else class="transactions-table-container">
      <table class="transactions-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Account</th>
            <th>Stock</th>
            <th>Type</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Fees</th>
            <th>Total Value</th>
            <th>Notes</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="transaction in transactions" :key="transaction.id">
            <td>{{ formatDate(transaction.transaction_date) }}</td>
            <td>{{ transaction.account_name }}</td>
            <td><strong>{{ transaction.stock_symbol }}</strong></td>
            <td>
              <span :class="['type-badge', transaction.transaction_type === 'BUY' ? 'buy' : 'sell']">
                {{ transaction.transaction_type }}
              </span>
            </td>
            <td>{{ transaction.quantity }}</td>
            <td>{{ formatCurrency(transaction.price) }}</td>
            <td>{{ formatCurrency(transaction.fees) }}</td>
            <td>{{ formatCurrency(transaction.total_value) }}</td>
            <td>{{ transaction.notes || '-' }}</td>
            <td>
              <button @click="deleteTransaction(transaction.id)" class="btn-danger-small">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Transaction Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <h2>Add Transaction</h2>

        <form @submit.prevent="submitTransaction">
          <div class="form-group">
            <label for="account">Account *</label>
            <select
              id="account"
              v-model.number="formData.account_id"
              required
            >
              <option :value="null">Select an account</option>
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="stock">Stock *</label>
            <select
              id="stock"
              v-model.number="formData.stock_id"
              required
            >
              <option :value="null">Select a stock</option>
              <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
                {{ stock.symbol }} - {{ stock.name }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Transaction Type *</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="formData.transaction_type" value="BUY" /> Buy
                </label>
                <label>
                  <input type="radio" v-model="formData.transaction_type" value="SELL" /> Sell
                </label>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="quantity">Quantity *</label>
              <input
                id="quantity"
                v-model.number="formData.quantity"
                type="number"
                step="0.01"
                required
              />
            </div>

            <div class="form-group">
              <label for="price">Price *</label>
              <input
                id="price"
                v-model.number="formData.price"
                type="number"
                step="0.01"
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="transaction_date">Transaction Date *</label>
              <input
                id="transaction_date"
                v-model="formData.transaction_date"
                type="datetime-local"
                required
              />
            </div>

            <div class="form-group">
              <label for="fees">Fees</label>
              <input
                id="fees"
                v-model.number="formData.fees"
                type="number"
                step="0.01"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="notes">Notes</label>
            <textarea
              id="notes"
              v-model="formData.notes"
              rows="2"
            ></textarea>
          </div>

          <div class="modal-actions">
            <button type="button" @click="showAddModal = false" class="btn-secondary">Cancel</button>
            <button type="button" @click="submitAndReset" class="btn-success" :disabled="loading">
              {{ loading ? 'Saving...' : 'Add & New' }}
            </button>
            <button type="submit" class="btn-primary" :disabled="loading">
              {{ loading ? 'Saving...' : 'Add Transaction' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Bulk Upload Modal -->
    <div v-if="showBulkUploadModal" class="modal-overlay" @click.self="showBulkUploadModal = false">
      <div class="modal-content large-modal">
        <h2>Bulk Upload Transactions from CSV</h2>

        <div class="upload-info">
          <p>Upload a CSV file with your transactions. The file should have the following columns:</p>
          <p><strong>account, stock_symbol, transaction_type, quantity, price, transaction_date, fees (optional), notes (optional)</strong></p>
          <button @click="downloadTemplate" class="btn-link">Download CSV Template</button>
        </div>

        <div class="file-upload-section">
          <input
            type="file"
            accept=".csv"
            @change="handleFileSelect"
            id="csv-file"
            class="file-input"
          />
          <label for="csv-file" class="file-label">
            {{ csvFile ? csvFile.name : 'Choose CSV file...' }}
          </label>
        </div>

        <div v-if="csvErrors.length > 0" class="error-list">
          <h4>Errors:</h4>
          <ul>
            <li v-for="(err, idx) in csvErrors" :key="idx">{{ err }}</li>
          </ul>
        </div>

        <div v-if="csvData.length > 0" class="preview-section">
          <h3>Preview ({{ csvData.length }} transactions)</h3>
          <div class="preview-table-container">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Stock</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Fees</th>
                  <th>Date</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in csvData" :key="idx">
                  <td>{{ item.account_name }}</td>
                  <td>{{ item.stock_symbol }}</td>
                  <td>
                    <span :class="['type-badge', item.transaction_type === 'BUY' ? 'buy' : 'sell']">
                      {{ item.transaction_type }}
                    </span>
                  </td>
                  <td>{{ item.quantity }}</td>
                  <td>{{ formatCurrency(item.price) }}</td>
                  <td>{{ formatCurrency(item.fees) }}</td>
                  <td>{{ item.transaction_date }}</td>
                  <td>{{ item.notes || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" @click="showBulkUploadModal = false" class="btn-secondary">Cancel</button>
          <button
            type="button"
            @click="submitBulkTransactions"
            class="btn-primary"
            :disabled="csvData.length === 0 || uploadLoading"
          >
            {{ uploadLoading ? 'Uploading...' : `Upload ${csvData.length} Transactions` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transactions-page {
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

.filter-section {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-section label {
  font-weight: 500;
  color: #2c3e50;
  white-space: nowrap;
}

.filter-section select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  min-width: 200px;
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
}

.btn-success {
  background-color: #27ae60;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-success:hover:not(:disabled) {
  background-color: #229954;
}

.btn-success:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger-small {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.error-message {
  background-color: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.transactions-table-container {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
}

.transactions-table th,
.transactions-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.transactions-table th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.type-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge.buy {
  background-color: #d4edda;
  color: #155724;
}

.type-badge.sell {
  background-color: #f8d7da;
  color: #721c24;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h2 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;
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
}

.radio-group {
  display: flex;
  gap: 1rem;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
}

.form-hint {
  display: block;
  margin-top: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}

.form-hint a {
  color: #3498db;
  text-decoration: none;
}

.form-hint a:hover {
  text-decoration: underline;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.large-modal {
  max-width: 1000px;
}

.upload-info {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.upload-info p {
  margin: 0.5rem 0;
  color: #666;
}

.btn-link {
  background: none;
  border: none;
  color: #3498db;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.btn-link:hover {
  color: #2980b9;
}

.file-upload-section {
  margin-bottom: 1.5rem;
}

.file-input {
  display: none;
}

.file-label {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background-color: #3498db;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.file-label:hover {
  background-color: #2980b9;
}

.error-list {
  background-color: #fee;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.error-list h4 {
  margin: 0 0 0.5rem 0;
  color: #c00;
}

.error-list ul {
  margin: 0;
  padding-left: 1.5rem;
  color: #c00;
}

.preview-section {
  margin-bottom: 1.5rem;
}

.preview-section h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.preview-table-container {
  max-height: 400px;
  overflow: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.preview-table th,
.preview-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.preview-table th {
  background-color: #f5f5f5;
  position: sticky;
  top: 0;
  font-weight: 600;
  color: #2c3e50;
  text-transform: uppercase;
  font-size: 0.85rem;
}

.preview-table tbody tr:hover {
  background-color: #f9f9f9;
}
</style>

