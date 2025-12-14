<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { accountApi } from '@/services/api'
import type { Account } from '@/types'

const router = useRouter()
const accounts = ref<Account[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const loadAccounts = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await accountApi.getAll()
    accounts.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load accounts'
    console.error('Error loading accounts:', err)
  } finally {
    loading.value = false
  }
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
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-size: 1.1rem;
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.account-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.account-info h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.3rem;
}

.account-info .description {
  color: #666;
  margin: 0;
  font-size: 0.9rem;
}

.account-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}
</style>
