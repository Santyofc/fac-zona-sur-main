import { ref, onMounted, onUnmounted } from 'vue'

/**
 * useMotion — Centralized Mouse Tracking & Motion Engine
 * Complements the Zero-Leak Policy by using a single event listener.
 */
export function useMotion() {
  const x = ref(0)
  const y = ref(0)
  const isMoving = ref(false)
  let timeout: any = null

  const handleMouseMove = (e: MouseEvent) => {
    x.value = e.clientX
    y.value = e.clientY
    isMoving.value = true

    clearTimeout(timeout)
    timeout = setTimeout(() => {
      isMoving.value = false
    }, 2000)
  }

  // Smoothing/Spring logic could be added here if needed

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('mousemove', handleMouseMove)
    }
  })

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('mousemove', handleMouseMove)
      clearTimeout(timeout)
    }
  })

  return {
    x,
    y,
    isMoving,
  }
}
