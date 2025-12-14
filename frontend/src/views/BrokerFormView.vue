<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { brokerApi } from '@/services/api'

const router = useRouter()
const route = useRoute()

const isEditMode = ref(false)
const brokerId = ref<number | null>(null)
const formData = ref({
  name: '',
  description: ''
})
const loading = ref(false)
const error = ref<string | null>(null)

const loadBroker = async (id: number) => {
  loading.value = true
  try {
    const response = await brokerApi.getById(id)
    formData.value = {
      name: response.data.name,
      description: response.data.description || ''
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load broker'
    console.error('Error loading broker:', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    error.value = 'Broker name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    if (isEditMode.value && brokerId.value) {
      await brokerApi.update(brokerId.value, formData.value)
    } else {
      await brokerApi.create(formData.value)
    }
    router.push('/brokers')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to save broker'
    console.error('Error saving broker:', err)
  } finally {
    loading.value = false
  }
}

const cancel = () => {
  router.push('/brokers')
}

onMounted(() => {
  if (route.params.id) {
    isEditMode.value = true
    brokerId.value = parseInt(route.params.id as string)
    loadBroker(brokerId.value)
  }
})
</script>

<template>
  <div class="broker-form-page">
    <div class="form-container">
      <h1>{{ isEditMode ? 'Edit Broker' : 'Add Broker' }}</h1>

      <div v-if="error" class="error-message">{{ error }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="name">Broker Name *</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            placeholder="e.g., Zerodha, Robinhood"
            required
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="formData.description"
            placeholder="Optional description about this broker"
            rows="3"
            :disabled="loading"
          ></textarea>
        </div>

        <div class="form-actions">
          <button type="button" @click="cancel" class="btn-secondary" :disabled="loading">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Saving...' : (isEditMode ? 'Update Broker' : 'Add Broker') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.broker-form-page {
  max-width: 600px;
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
.form-group textarea:focus {
  outline: none;
  border-color: #42b983;
}

.form-group input:disabled,
.form-group textarea:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
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
</style>
