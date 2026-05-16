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
          <td>{{ event.related_stock_symbol }}</td>
          <td>{{ event.parent_cost_pct }}</td>
          <td>{{ event.demerged_cost_pct }}</td>
          <td>{{ event.notes }}</td>
          <td>
            <button class="btn-edit" @click="openEditModal(event)">Edit</button>
            <button class="btn-delete" @click="deleteEvent(event.id!)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else>No corporate events found.</div>
  </div>

  <!-- Edit Modal -->
  <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
    <div class="modal-content">
      <h3>Edit Corporate Event</h3>
      <form @submit.prevent="updateEvent" class="event-form">
        <div>
          <label>Stock:</label>
          <select v-model.number="editForm.stock_id" required>
            <option :value="0" disabled>Select Stock</option>
            <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
              {{ stock.symbol }} - {{ stock.name }}
            </option>
          </select>
        </div>
        <div>
          <label>Type:</label>
          <select v-model="editForm.event_type" required>
            <option value="" disabled>Select Type</option>
            <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>
        <div>
          <label>Date:</label>
          <input type="date" v-model="editForm.event_date" required />
        </div>
        <div>
          <label>Ratio:</label>
          <input type="number" step="any" v-model.number="editForm.ratio" />
        </div>
        <div>
          <label>Related Stock:</label>
          <select v-model.number="editForm.related_stock_id">
            <option :value="null">None</option>
            <option v-for="stock in stocks" :key="stock.id" :value="stock.id">
              {{ stock.symbol }} - {{ stock.name }}
            </option>
          </select>
        </div>
        <div>
          <label>Parent Cost %:</label>
          <input type="number" step="any" v-model.number="editForm.parent_cost_pct" />
        </div>
        <div>
          <label>Demerged/Merged Cost %:</label>
          <input type="number" step="any" v-model.number="editForm.demerged_cost_pct" />
        </div>
        <div>
          <label>Notes:</label>
          <input type="text" v-model="editForm.notes" />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="showEditModal = false">Cancel</button>
          <button type="submit" :disabled="submitting">{{ submitting ? 'Saving...' : 'Save Changes' }}</button>
        </div>
        <span v-if="error" class="error">{{ error }}</span>
      </form>
    </div>
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
  related_stock_id: null,
  parent_cost_pct: null,
  demerged_cost_pct: null,
  notes: ''
})
const submitting = ref(false)
const error = ref<string | null>(null)
const editingEvent = ref<CorporateEvent | null>(null)
const showEditModal = ref(false)
const editForm = ref<CorporateEvent>({
  stock_id: 0,
  event_type: '',
  event_date: '',
  ratio: null,
  related_stock_id: null,
  parent_cost_pct: null,
  demerged_cost_pct: null,
  notes: ''
})
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
    if (!payload.related_stock_id) payload.related_stock_id = null
    await corporateEventApi.create(payload)
    fetchEvents()
    resetForm()
  } catch (e: unknown) {
    error.value = (e as {response?: {data?: string}})?.response?.data || 'Failed to create event'
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
const openEditModal = (event: CorporateEvent) => {
  editingEvent.value = event
  editForm.value = {
    stock_id: event.stock_id,
    event_type: event.event_type,
    event_date: event.event_date,
    ratio: event.ratio ?? null,
    related_stock_id: event.related_stock_id ?? null,
    parent_cost_pct: event.parent_cost_pct ?? null,
    demerged_cost_pct: event.demerged_cost_pct ?? null,
    notes: event.notes ?? ''
  }
  showEditModal.value = true
}
const updateEvent = async () => {
  if (!editingEvent.value?.id) return
  error.value = null
  submitting.value = true
  try {
    const payload = { ...editForm.value }
    if (!payload.ratio) payload.ratio = null
    if (!payload.related_stock_id) payload.related_stock_id = null
    await corporateEventApi.update(editingEvent.value.id, payload)
    showEditModal.value = false
    editingEvent.value = null
    fetchEvents()
  } catch (e: unknown) {
    error.value = (e as {response?: {data?: string}})?.response?.data || 'Failed to update event'
  } finally {
    submitting.value = false
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
.event-form .modal-actions button {
  margin-top: 0;
  flex: 1;
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

.btn-edit {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  margin-right: 0.4rem;
}
.btn-edit:hover {
  background-color: #2980b9;
}
.btn-delete {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-delete:hover {
  background-color: #c0392b;
}
.btn-cancel {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.btn-cancel:hover {
  background-color: #7f8c8d;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: var(--bg-secondary, #fff);
  border-radius: 8px;
  padding: 2rem;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.modal-content h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: var(--text-primary, #2c3e50);
}
.modal-actions {
  display: flex;
  flex-direction: row;
  flex: 1 1 100%;
  gap: 1rem;
  align-items: center;
  margin-top: 0.5rem;
}

.modal-content .event-form > div {
  flex: 1 1 calc(50% - 0.5rem);
  max-width: calc(50% - 0.5rem);
  box-sizing: border-box;
}

.modal-content .event-form .modal-actions {
  flex: 1 1 100%;
  max-width: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
}

@media (prefers-color-scheme: dark) {
  .modal-content {
    background: #232526;
    color: #f1f1f1;
  }
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
