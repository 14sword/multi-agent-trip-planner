<template>
  <!-- Mobile backdrop -->
  <transition name="fade">
    <div v-if="open" class="sidebar-backdrop" @click="$emit('close')"></div>
  </transition>

  <aside class="sidebar" :class="{ 'sidebar--open': open }">
    <div class="sidebar-header">
      <router-link to="/" class="sidebar-brand" @click="$emit('close')">
        <span class="brand-icon">✦</span>
        <span class="brand-text">Voyager</span>
        <span class="brand-sub">Voyager</span>
      </router-link>
    </div>

    <nav class="sidebar-nav">
      <router-link
        to="/"
        class="sidebar-link"
        :class="{ active: $route.name === 'home' }"
        @click="$emit('close')"
      >
        <svg class="link-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>规划行程</span>
      </router-link>

      <router-link
        v-if="hasTrip"
        to="/result"
        class="sidebar-link"
        :class="{ active: $route.name === 'result' }"
        @click="$emit('close')"
      >
        <svg class="link-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <span>当前行程</span>
      </router-link>

      <router-link
        to="/favorites"
        class="sidebar-link"
        :class="{ active: $route.name === 'favorites' }"
        @click="$emit('close')"
      >
        <svg class="link-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span>我的收藏</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="footer-info">
        <span class="footer-version">v1.0</span>
        <span class="footer-divider">·</span>
        <span>AI Agent</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

const hasTrip = computed(() => {
  try {
    const data = sessionStorage.getItem('tripPlan')
    return !!data && JSON.parse(data)?.days?.length > 0
  } catch {
    return false
  }
})
</script>

<style scoped>
.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 199;
  backdrop-filter: blur(2px);
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 240px;
  background: var(--color-paper);
  border-right: 1px solid rgba(232, 226, 218, 0.5);
  z-index: 200;
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.sidebar-header {
  padding: var(--space-lg) var(--space-lg) var(--space-md);
  border-bottom: 1px solid rgba(232, 226, 218, 0.4);
}

.sidebar-brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
  text-decoration: none;
  color: var(--color-charcoal);
}

.brand-icon {
  color: var(--color-terracotta);
  font-size: 1.1rem;
  font-family: var(--font-display);
}

.brand-text {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 600;
}

.brand-sub {
  font-family: var(--font-body);
  font-size: 0.7rem;
  color: var(--color-warm-gray);
  letter-spacing: 0.05em;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-md) var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  text-decoration: none;
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-warm-gray);
  transition: all var(--transition-fast);
}

.sidebar-link:hover {
  background: rgba(196, 101, 74, 0.05);
  color: var(--color-charcoal);
}

.sidebar-link.active {
  background: rgba(196, 101, 74, 0.08);
  color: var(--color-terracotta);
  font-weight: 600;
}

.link-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.sidebar-link.active .link-icon {
  opacity: 1;
}

.sidebar-footer {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid rgba(232, 226, 218, 0.4);
}

.footer-info {
  font-size: 0.7rem;
  color: var(--color-light-gray);
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-version {
  font-weight: 600;
  color: var(--color-warm-gray);
}

/* Mobile */
@media (max-width: 768px) {
  .sidebar-backdrop {
    display: block;
  }

  .sidebar--open {
    box-shadow: var(--shadow-dramatic);
  }
}

/* All sizes: show when open */
.sidebar--open {
  transform: translateX(0);
}
</style>
