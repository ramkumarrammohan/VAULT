<script setup lang="ts">
import { RouterView } from 'vue-router'
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
        </div>
      </div>
    </nav>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
    'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #f5f5f5;
}

#app {
  min-height: 100vh;
}

.navbar {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
  color: white;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  transition: opacity 0.3s;
}

.nav-links a:hover {
  opacity: 0.8;
}

.nav-links a.router-link-active {
  border-bottom: 2px solid #42b983;
}

main {
  min-height: calc(100vh - 70px);
}
</style>
