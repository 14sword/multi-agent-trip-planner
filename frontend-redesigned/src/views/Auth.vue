<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <span class="auth-icon">✦</span>
        <h1 class="auth-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h1>
        <p class="auth-subtitle">{{ isLogin ? '登录以保存和管理你的行程' : '注册后即可收藏和分享行程' }}</p>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="your@email.com"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="至少6位"
            minlength="6"
            required
          />
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button type="submit" class="auth-submit" :disabled="submitting">
          {{ submitting ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <div class="auth-switch">
        <span>{{ isLogin ? '没有账号？' : '已有账号？' }}</span>
        <button class="switch-btn" @click="isLogin = !isLogin; error = ''">
          {{ isLogin ? '注册' : '登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ApiError } from '@/services/api'

const router = useRouter()
const route = useRoute()
const isLogin = ref(true)
const email = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    const endpoint = isLogin.value ? '/api/auth/login' : '/api/auth/register'
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.detail || '操作失败'
      return
    }
    localStorage.setItem('auth_token', data.token)
    localStorage.setItem('user_email', data.email)
    window.dispatchEvent(new Event('auth-changed'))
    router.push((route.query.redirect as string) || '/')
  } catch (e: any) {
    error.value = e instanceof ApiError ? e.message : '网络请求失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-cream, #fffcf7);
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 16px;
  padding: 40px 32px;
  border: 1px solid rgba(232,226,218,0.5);
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-icon {
  font-size: 1.5rem;
  color: #c67b5c;
}

.auth-title {
  font-family: var(--font-display, 'Cormorant Garamond', serif);
  font-size: 1.6rem;
  font-weight: 600;
  color: #2c2520;
  margin: 8px 0 4px;
}

.auth-subtitle {
  color: #8a7e75;
  font-size: 0.85rem;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #5a524a;
}

.form-input {
  padding: 10px 14px;
  border: 1px solid rgba(232,226,218,0.8);
  border-radius: 8px;
  font-size: 0.9rem;
  color: #2c2520;
  background: #faf8f5;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: #c67b5c;
}

.form-error {
  color: #d44;
  font-size: 0.8rem;
  margin: 0;
}

.auth-submit {
  padding: 12px;
  background: #c67b5c;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.auth-submit:hover {
  opacity: 0.9;
}

.auth-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: 20px;
  font-size: 0.85rem;
  color: #8a7e75;
}

.switch-btn {
  background: none;
  border: none;
  color: #c67b5c;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.85rem;
}
</style>
