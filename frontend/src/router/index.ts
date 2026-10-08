import CorporateEventsView from '@/views/CorporateEventsView.vue'
import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import AccountsView from '@/views/AccountsView.vue'
import AccountFormView from '@/views/AccountFormView.vue'
import StocksView from '@/views/StocksView.vue'
import StockFormView from '@/views/StockFormView.vue'
import TransactionsView from '@/views/TransactionsView.vue'
import MutualFundsView from '@/views/MutualFundsView.vue'
import MutualFundFormView from '@/views/MutualFundFormView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: AccountsView
    },
    {
      path: '/accounts/add',
      name: 'account-add',
      component: AccountFormView
    },
    {
      path: '/accounts/edit/:id',
      name: 'account-edit',
      component: AccountFormView
    },
    {
      path: '/stocks',
      name: 'stocks',
      component: StocksView
    },
    {
      path: '/stocks/add',
      name: 'stock-add',
      component: StockFormView
    },
    {
      path: '/stocks/edit/:id',
      name: 'stock-edit',
      component: StockFormView
    },
    {
      path: '/transactions',
      name: 'transactions',
      component: TransactionsView
    },
    {
      path: '/corporate-events',
      name: 'corporate-events',
      component: CorporateEventsView
    },
    {
      path: '/mutual-funds',
      name: 'mutual-funds',
      component: MutualFundsView
    },
    {
      path: '/mutual-funds/add',
      name: 'mutual-fund-add',
      component: MutualFundFormView
    },
    {
      path: '/mutual-funds/edit/:id',
      name: 'mutual-fund-edit',
      component: MutualFundFormView
    }
  ],
})

export default router
