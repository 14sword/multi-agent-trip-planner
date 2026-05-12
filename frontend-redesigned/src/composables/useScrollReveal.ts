import { onMounted, onUnmounted, ref, type Ref } from 'vue'

export function useScrollReveal<T extends HTMLElement>(
  options: IntersectionObserverInit = {}
): { elementRef: Ref<T | null>; isVisible: Ref<boolean> } {
  const elementRef = ref<T | null>(null) as Ref<T | null>
  const isVisible = ref(false)
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!elementRef.value) return

    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer?.unobserve(entry.target)
        }
      },
      { threshold: 0.1, ...options }
    )

    observer.observe(elementRef.value)
  })

  onUnmounted(() => {
    observer?.disconnect()
  })

  return { elementRef, isVisible }
}
