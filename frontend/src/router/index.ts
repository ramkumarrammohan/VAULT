import CorporateEventsView from '@/views/CorporateEventsView.vue'
import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import AccountsView from '@/views/AccountsView.vue'
import AccountFormView from '@/views/AccountFormView.vue'
import StocksView from '@/views/StocksView.vue'
import StockFormView from '@/views/StockFormView.vue'
import HoldingFormView from '@/views/HoldingFormView.vue'
import TransactionsView from '@/views/TransactionsView.vue'

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
      path: '/holdings/add',
      name: 'holding-add',
      component: HoldingFormView
    },
    {
      path: '/holdings/edit/:id',
      name: 'holding-edit',
      component: HoldingFormView
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
    }
  ],
})

export default router
