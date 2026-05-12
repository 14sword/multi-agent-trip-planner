<template>
  <div class="weather-grid">
    <div
      v-for="info in weather"
      :key="info.date"
      :class="['weather-card', getWeatherClass(info.day_weather)]"
    >
      <div class="weather-date">{{ formatWeatherDate(info.date) }}</div>
      <div class="weather-icon">{{ getWeatherEmoji(info.day_weather) }}</div>
      <div class="weather-condition">{{ info.day_weather }}</div>
      <div class="weather-temps">
        <span class="temp-high">{{ info.day_temp }}°</span>
        <span class="temp-sep">/</span>
        <span class="temp-low">{{ info.night_temp }}°</span>
      </div>
      <div class="weather-wind">{{ info.wind_direction }} {{ info.wind_power }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WeatherInfo } from '@/types'

defineProps<{ weather: WeatherInfo[] }>()

const getWeatherEmoji = (w: string) => {
  if (w.includes('晴')) return '☀️'
  if (w.includes('阴')) return '☁️'
  if (w.includes('雨')) return '🌧️'
  if (w.includes('雪')) return '❄️'
  if (w.includes('雾')) return '🌫️'
  return '🌤️'
}

const getWeatherClass = (w: string) => {
  if (w.includes('晴')) return 'weather--sunny'
  if (w.includes('雨')) return 'weather--rainy'
  if (w.includes('雪')) return 'weather--snowy'
  return 'weather--cloudy'
}

const formatWeatherDate = (d: string) => {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style scoped>
.weather-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--space-md);
}

.weather-card {
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  text-align: center;
  transition: all var(--transition-normal);
  border: 1px solid transparent;
}

.weather-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card);
}

.weather--sunny {
  background: linear-gradient(135deg, #FFF8E7 0%, var(--color-paper) 100%);
  border-color: rgba(232, 152, 94, 0.15);
}

.weather--rainy {
  background: linear-gradient(135deg, #EDF5F0 0%, var(--color-paper) 100%);
  border-color: rgba(82, 121, 111, 0.15);
}

.weather--snowy {
  background: linear-gradient(135deg, #F0F4F8 0%, var(--color-paper) 100%);
  border-color: rgba(107, 101, 96, 0.12);
}

.weather--cloudy {
  background: linear-gradient(135deg, #F5F3F0 0%, var(--color-paper) 100%);
  border-color: rgba(232, 226, 218, 0.4);
}

.weather-date {
  font-size: 0.8rem;
  color: var(--color-warm-gray);
  font-weight: 500;
  margin-bottom: 8px;
}

.weather-icon {
  font-size: 2rem;
  margin-bottom: 6px;
}

.weather-condition {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: 6px;
}

.weather-temps {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 4px;
}

.temp-high {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-charcoal);
}

.temp-sep {
  color: var(--color-light-gray);
  font-size: 0.9rem;
}

.temp-low {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-warm-gray);
}

.weather-wind {
  font-size: 0.7rem;
  color: var(--color-warm-gray);
}
</style>
