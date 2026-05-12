<template>
  <div id="wanderlust-app">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
#wanderlust-app {
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
