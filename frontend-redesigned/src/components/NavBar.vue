<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <div class="navbar-left">
        <button class="navbar-menu-btn" @click="$emit('toggleSidebar')" aria-label="菜单">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <router-link to="/" class="navbar-brand">
          <span class="brand-icon">✦</span>
          <span class="brand-text">Voyager</span>
        </router-link>
      </div>
      <div class="navbar-right">
        <button v-if="userEmail" class="user-btn" @click="showMenu = !showMenu">
          <span class="user-avatar">{{ userEmail.charAt(0).toUpperCase() }}</span>
        </button>
        <router-link v-else to="/login" class="login-btn">登录</router-link>
        <div v-if="showMenu && userEmail" class="user-menu">
          <div class="menu-email">{{ userEmail }}</div>
          <button class="menu-item" @click="logout">退出登录</button>
        </div>
        <button
          v-show="showBackTop"
          class="back-top-btn"
          @click="scrollToTop"
          aria-label="回到顶部"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="18 15 12 9 6 15"/>
          </svg>
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

defineEmits<{ toggleSidebar: [] }>()

const router = useRouter()
const showBackTop = ref(false)
const userEmail = ref(localStorage.getItem('user_email') || '')
const showMenu = ref(false)

const onScroll = () => {
  showBackTop.value = window.scrollY > 400
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const onAuthChanged = () => {
  userEmail.value = localStorage.getItem('user_email') || ''
}

const logout = () => {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_email')
  userEmail.value = ''
  showMenu.value = false
  window.dispatchEvent(new Event('auth-changed'))
  router.push('/')
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('auth-changed', onAuthChanged)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('auth-changed', onAuthChanged)
})
</script>

<style scoped>
.navbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(252, 249, 245, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(232, 226, 218, 0.4);
}

.navbar-inner {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 var(--space-xl);
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.navbar-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-charcoal);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.navbar-menu-btn:hover {
  background: rgba(196, 101, 74, 0.08);
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--color-charcoal);
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 600;
}

.brand-icon {
  color: var(--color-terracotta);
  font-size: 1rem;
}

.back-top-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1.5px solid var(--color-light-gray);
  border-radius: 50%;
  background: var(--color-paper);
  color: var(--color-warm-gray);
  cursor: pointer;
  transition: all var(--transition-fast);
  animation: fadeIn 0.3s ease;
}

.back-top-btn:hover {
  border-color: var(--color-terracotta);
  color: var(--color-terracotta);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(196, 101, 74, 0.15);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.login-btn {
  padding: 6px 16px;
  background: var(--color-terracotta, #c67b5c);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  text-decoration: none;
  transition: opacity 0.2s;
}

.login-btn:hover {
  opacity: 0.9;
}

.user-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-terracotta, #c67b5c);
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.user-menu {
  position: absolute;
  top: 44px;
  right: 0;
  background: white;
  border: 1px solid rgba(232,226,218,0.5);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  min-width: 160px;
  z-index: 200;
  overflow: hidden;
}

.menu-email {
  padding: 10px 14px;
  font-size: 0.8rem;
  color: #8a7e75;
  border-bottom: 1px solid rgba(232,226,218,0.5);
}

.menu-item {
  display: block;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  text-align: left;
  font-size: 0.85rem;
  color: #2c2520;
  cursor: pointer;
}

.menu-item:hover {
  background: #f5f0eb;
}

@media (max-width: 768px) {
  .navbar-inner {
    padding: 0 var(--space-md);
    height: 48px;
  }

  .brand-text {
    font-size: 1rem;
  }
}
</style>
