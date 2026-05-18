import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import ComparisonView from '@/views/ComparisonView.vue'
import Result from '@/views/Result.vue'
import Favorites from '@/views/Favorites.vue'
import Share from '@/views/Share.vue'
import Auth from '@/views/Auth.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/compare',
      name: 'compare',
      component: ComparisonView,
    },
    {
      path: '/result',
      name: 'result',
      component: Result,
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: Favorites,
      meta: { requiresAuth: true },
    },
    {
      path: '/share/:token',
      name: 'share',
      component: Share,
    },
    {
      path: '/login',
      name: 'login',
      component: Auth,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('auth_token')) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
