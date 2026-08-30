<script setup lang="ts">
import type { ConsolidatedHolding } from '@/types'
import { formatCurrency } from '@/utils/currency'

const props = defineProps<{
  holdings: ConsolidatedHolding[]
  currency: string
  sortBy: string
  sortDirection: 'asc' | 'desc'
  expandedStocks: Set<number>
  getGainLossClass: (value: number) => string
}>()

const emit = defineEmits<{
  (e: 'sort', column: string): void
  (e: 'toggle-expand', stockId: number): void
}>()
</script>

<template>
  <table class="holdings-table">
    <thead>
      <tr>
        <th @click="emit('sort', 'stock_symbol')" class="sortable">
          Stock
          <span class="sort-indicator" v-if="sortBy === 'stock_symbol'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'quantity')" class="sortable">
          Quantity
          <span class="sort-indicator" v-if="sortBy === 'quantity'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'average_price')" class="sortable">
          Avg Price
          <span class="sort-indicator" v-if="sortBy === 'average_price'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'current_price')" class="sortable">
          Current Price
          <span class="sort-indicator" v-if="sortBy === 'current_price'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'invested_value')" class="sortable">
          Invested
          <span class="sort-indicator" v-if="sortBy === 'invested_value'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'current_value')" class="sortable">
          Current Value
          <span class="sort-indicator" v-if="sortBy === 'current_value'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
        <th @click="emit('sort', 'gain_loss')" class="sortable">
          Gain/Loss
          <span class="sort-indicator" v-if="sortBy === 'gain_loss'">
            {{ sortDirection === 'asc' ? '▲' : '▼' }}
          </span>
        </th>
      </tr>
    </thead>
    <tbody>
      <template v-for="holding in holdings" :key="holding.stock_id">
        <!-- Consolidated parent row -->
        <tr
          class="consolidated-row"
          :class="{ expanded: expandedStocks.has(holding.stock_id) }"
          @click="emit('toggle-expand', holding.stock_id)"
        >
          <td>
            <span class="expand-chevron">{{ expandedStocks.has(holding.stock_id) ? '▼' : '▶' }}</span>
            <strong>{{ holding.stock_symbol }}</strong>
            <br />
            <small>{{ holding.stock_name }}</small>
          </td>
          <td>{{ holding.quantity }}</td>
          <td>{{ formatCurrency(holding.average_price, currency) }}</td>
          <td>{{ holding.current_price ? formatCurrency(holding.current_price, currency) : 'N/A' }}</td>
          <td>{{ formatCurrency(holding.invested_value, currency) }}</td>
          <td>{{ formatCurrency(holding.current_value, currency) }}</td>
          <td :class="getGainLossClass(holding.gain_loss)">
            {{ formatCurrency(holding.gain_loss, currency) }}
            <br />
            <small>({{ holding.gain_loss_percentage.toFixed(2) }}%)</small>
          </td>
        </tr>
        <!-- Per-account sub-rows -->
        <template v-if="expandedStocks.has(holding.stock_id)">
          <tr
            v-for="sub in holding.sub_holdings"
            :key="sub.account_id + '-' + sub.stock_id"
            class="sub-row"
          >
            <td class="sub-account-cell">
              <span class="sub-indent">└</span>
              {{ sub.account_name }}
            </td>
            <td>{{ sub.quantity }}</td>
            <td>{{ formatCurrency(sub.average_price, currency) }}</td>
            <td>{{ sub.current_price ? formatCurrency(sub.current_price, currency) : 'N/A' }}</td>
            <td>{{ formatCurrency(sub.invested_value, currency) }}</td>
            <td>{{ formatCurrency(sub.current_value, currency) }}</td>
            <td :class="getGainLossClass(sub.gain_loss)">
              {{ formatCurrency(sub.gain_loss, currency) }}
              <br />
              <small>({{ sub.gain_loss_percentage.toFixed(2) }}%)</small>
            </td>
          </tr>
        </template>
      </template>
    </tbody>
  </table>
</template>

<style scoped>
.holdings-table {
  width: 100%;
  border-collapse: collapse;
}

.holdings-table th,
.holdings-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.holdings-table th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.holdings-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.holdings-table th.sortable:hover {
  background-color: #e8e8e8;
}

.sort-indicator {
  display: inline-block;
  margin-left: 0.5rem;
  font-size: 0.8rem;
  color: #42b983;
}

.holdings-table tbody tr:hover {
  background-color: #f9f9f9;
}

.consolidated-row {
  cursor: pointer;
}

.consolidated-row:hover {
  background-color: #f0f7f4 !important;
}

.consolidated-row.expanded {
  background-color: #e8f5ee;
}

.expand-chevron {
  display: inline-block;
  margin-right: 0.5rem;
  font-size: 0.75rem;
  color: #42b983;
}

.sub-row {
  background-color: #fafafa;
}

.sub-row:hover {
  background-color: #f0f0f0 !important;
}

.sub-row td {
  font-size: 0.9rem;
  color: #555;
  border-bottom: 1px solid #efefef;
}

.sub-account-cell {
  padding-left: 1.5rem !important;
}

.sub-indent {
  color: #42b983;
  margin-right: 0.4rem;
}

.holdings-table td strong {
  color: #2c3e50;
}

.holdings-table td small {
  color: #666;
  font-size: 0.85rem;
}

.positive { color: #42b983; }
.negative { color: #e74c3c; }
.neutral  { color: #666; }
</style>
