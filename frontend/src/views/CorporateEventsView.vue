<template>
  <div class="corporate-events-view">
    <h2>Corporate Events</h2>
    <form @submit.prevent="createEvent" class="event-form">
      <div>
        <label>Stock:</label>
        <select v-model.number="form.stock_id" required>
          <option :value="0" disabled>Select Stock</option>
          <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
            {{ stock.symbol }} - {{ stock.name }}
          </option>
        </select>
      </div>
      <div>
        <label>Type:</label>
        <select v-model="form.event_type" required>
          <option value="">Select Type</option>
          <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
      <div>
        <label>Date:</label>
        <input type="date" v-model="form.event_date" required />
      </div>
      <div>
        <label>Ratio:</label>
        <input type="number" step="any" v-model.number="form.ratio" />
      </div>
      <div>
        <label>Quantity:</label>
        <input type="number" step="any" v-model.number="form.quantity" />
      </div>
      <div>
        <label>Amount:</label>
        <input type="number" step="any" v-model.number="form.amount" />
      </div>
      <div>
        <label>Related Stock:</label>
        <select v-model.number="form.related_stock_id">
          <option :value="null">None</option>
          <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
            {{ stock.symbol }} - {{ stock.name }}
          </option>
        </select>
      </div>
      <div>
        <label>Parent Cost %:</label>
        <input type="number" step="any" v-model.number="form.parent_cost_pct" placeholder="e.g. 86.49" />
      </div>
      <div>
        <label>Demerged/Merged Cost %:</label>
        <input type="number" step="any" v-model.number="form.demerged_cost_pct" placeholder="e.g. 13.51" />
      </div>
      <div>
        <label>Notes:</label>
        <input type="text" v-model="form.notes" />
      </div>
      <button type="submit" :disabled="submitting">Add Event</button>
      <span v-if="error" class="error">{{ error }}</span>
    </form>

    <button @click="fetchEvents">Refresh</button>
    <table v-if="events.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>Stock</th>
          <th>Type</th>
          <th>Date</th>
          <th>Ratio</th>
          <th>Quantity</th>
          <th>Amount</th>
          <th>Related Stock</th>
          <th>Parent Cost %</th>
          <th>Demerged/Merged Cost %</th>
          <th>Notes</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="event in events" :key="event.id">
          <td>{{ event.id }}</td>
          <td>{{ event.stock_symbol }}</td>
          <td>{{ event.event_type }}</td>
          <td>{{ event.event_date }}</td>
          <td>{{ event.ratio }}</td>
          <td>{{ event.quantity }}</td>
          <td>{{ event.amount }}</td>
          <td>{{ event.related_stock_symbol }}</td>
          <td>{{ event.parent_cost_pct }}</td>
          <td>{{ event.demerged_cost_pct }}</td>
          <td>{{ event.notes }}</td>
          <td>
            <button @click="deleteEvent(event.id)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else>No corporate events found.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { corporateEventApi, stockApi } from '../services/api'
import type { CorporateEvent, Stock } from '@/types'

const events = ref<CorporateEvent[]>([])
const stocks = ref<Stock[]>([])
const form = ref<CorporateEvent>({
  stock_id: 0,
  event_type: '',
  event_date: '',
  ratio: null,
  quantity: null,
  amount: null,
  related_stock_id: null,
  parent_cost_pct: null,
  demerged_cost_pct: null,
  notes: ''
})
const submitting = ref(false)
const error = ref<string | null>(null)
const eventTypes = [
  'SPLIT',
  'DEMERGER',
  'MERGER',
  'AMALGAMATION',
  'DIVIDEND',
  'NAME_CHANGE'
]

const fetchEvents = async () => {
  const res = await corporateEventApi.getAll()
  events.value = res.data
}
const fetchStocks = async () => {
  const res = await stockApi.getAll()
  stocks.value = res.data
}
const resetForm = () => {
  form.value = {
    stock_id: 0,
    event_type: '',
    event_date: '',
    ratio: null,
    quantity: null,
    amount: null,
    related_stock_id: null,
    parent_cost_pct: null,
    demerged_cost_pct: null,
    notes: ''
  }
}
const createEvent = async () => {
  error.value = null
  submitting.value = true
  try {
    const payload = { ...form.value }
    if (!payload.stock_id || !payload.event_type || !payload.event_date) {
      error.value = 'Stock, event type, and date are required.'
      submitting.value = false
      return
    }
    if (!payload.ratio) payload.ratio = null
    if (!payload.quantity) payload.quantity = null
    if (!payload.amount) payload.amount = null
    if (!payload.related_stock_id) payload.related_stock_id = null
    await corporateEventApi.create(payload)
    fetchEvents()
    resetForm()
  } catch (e: any) {
    error.value = e.response?.data || 'Failed to create event'
  } finally {
    submitting.value = false
  }
}
const deleteEvent = async (id: number) => {
  if (confirm('Delete this event?')) {
    await corporateEventApi.delete(id)
    fetchEvents()
  }
}
onMounted(() => {
  fetchEvents()
  fetchStocks()
})
</script>

<style scoped>
.corporate-events-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

h2 {
  font-size: 1.5rem;
  color: var(--text-primary, #2c3e50);
  margin-bottom: 1.5rem;
}

.event-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  background: var(--bg-secondary, #fff);
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-bottom: 2rem;
}
.event-form > div {
  flex: 1 1 200px;
  display: flex;
  flex-direction: column;
}
.event-form label {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: var(--text-primary, #2c3e50);
}
.event-form input,
.event-form select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  background: var(--bg-input, #fff);
  color: var(--text-primary, #2c3e50);
}
.event-form button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1.2rem;
  transition: background-color 0.3s;
}
.event-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.event-form .error {
  color: #e74c3c;
  margin-left: 1rem;
  font-size: 0.95rem;
}

button {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 0.5rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-bottom: 1rem;
}
button:hover:not(:disabled) {
  background-color: #7f8c8d;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background: var(--bg-secondary, #fff);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
}
th, td {
  border-bottom: 1px solid #e0e0e0;
  padding: 1rem;
  text-align: left;
}
th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: var(--text-primary, #2c3e50);
  font-size: 0.9rem;
  text-transform: uppercase;
}
tbody tr:hover {
  background-color: #f9f9f9;
}
.error {
  color: #e74c3c;
  margin-top: 0.5rem;
}

@media (prefers-color-scheme: dark) {
  .corporate-events-view {
    background: #181a1b;
  }
  .event-form,
  table {
    background: #232526;
    color: #f1f1f1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  th, td {
    color: #f1f1f1;
    border-bottom: 1px solid #333;
  }
  th {
    background-color: #232526;
  }
  tbody tr:hover {
    background-color: #232526;
  }
  .event-form input,
  .event-form select {
    background: #232526;
    color: #f1f1f1;
    border: 1px solid #444;
  }
  .event-form label {
    color: #f1f1f1;
  }
}
</style>
