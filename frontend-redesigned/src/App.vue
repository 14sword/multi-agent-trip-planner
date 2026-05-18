<template>
  <div id="voyager-app">
    <NavBar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    <SideBar :open="sidebarOpen" @close="sidebarOpen = false" />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import NavBar from '@/components/NavBar.vue'
import SideBar from '@/components/SideBar.vue'

const sidebarOpen = ref(false)
</script>

<style>
#voyager-app {
  min-height: 100vh;
}

.main-content {
  min-height: 100vh;
}

/* Page Transitions */
.page-enter-active {
  transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.page-leave-active {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
