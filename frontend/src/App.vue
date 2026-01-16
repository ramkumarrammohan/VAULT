<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'

const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  updateTheme()
}

const updateTheme = () => {
  if (isDark.value) {
    document.documentElement.classList.add('dark-theme')
  } else {
    document.documentElement.classList.remove('dark-theme')
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  isDark.value = savedTheme === 'dark'
  updateTheme()
})
</script>

<template>
  <div id="app">
    <nav class="navbar">
      <div class="container">
        <router-link to="/" class="logo">Portfolio Tracker</router-link>
        <div class="nav-links">
          <router-link to="/">Dashboard</router-link>
          <router-link to="/accounts">Accounts</router-link>
          <router-link to="/stocks">Stocks</router-link>
          <router-link to="/transactions">Transactions</router-link>
          <button @click="toggleTheme" class="theme-toggle" :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
            {{ isDark ? '☀️' : '🌙' }}
          </button>
        </div>
      </div>
    </nav>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style>
:root {
  --bg-primary: #f5f5f5;
  --bg-secondary: white;
  --bg-tertiary: #f9f9f9;
  --text-primary: #2c3e50;
  --text-secondary: #666;
  --border-color: #ddd;
  --border-light: #e0e0e0;
  --navbar-bg: #2c3e50;
  --navbar-text: white;
  --card-shadow: rgba(0, 0, 0, 0.1);
  --success-bg: #d4edda;
  --success-text: #155724;
  --danger-bg: #f8d7da;
  --danger-text: #721c24;
  --error-bg: #fee;
  --error-text: #c00;
  --table-hover: #f9f9f9;
  --input-bg: white;
  --modal-overlay: rgba(0, 0, 0, 0.5);
}

.dark-theme {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #363636;
  --text-primary: #e0e0e0;
  --text-secondary: #b0b0b0;
  --border-color: #404040;
  --border-light: #505050;
  --navbar-bg: #1a1a1a;
  --navbar-text: #e0e0e0;
  --card-shadow: rgba(0, 0, 0, 0.5);
  --success-bg: #1e4620;
  --success-text: #a3d9a5;
  --danger-bg: #4a1c1c;
  --danger-text: #f5a3a3;
  --error-bg: #4a1c1c;
  --error-text: #f5a3a3;
  --table-hover: #363636;
  --input-bg: #363636;
  --modal-overlay: rgba(0, 0, 0, 0.8);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
    'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s, color 0.3s;
}

#app {
  min-height: 100vh;
}

.navbar {
  background-color: var(--navbar-bg);
  color: var(--navbar-text);
  padding: 1rem 0;
  box-shadow: 0 2px 4px var(--card-shadow);
  transition: background-color 0.3s;
}

.navbar .container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar .logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--navbar-text);
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-links a {
  color: var(--navbar-text);
  text-decoration: none;
  transition: opacity 0.3s;
}

.nav-links a:hover {
  opacity: 0.8;
}

.nav-links a.router-link-active {
  border-bottom: 2px solid #42b983;
}

.theme-toggle {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  transition: transform 0.2s;
}

.theme-toggle:hover {
  transform: scale(1.1);
}

main {
  min-height: calc(100vh - 70px);
}
</style>
