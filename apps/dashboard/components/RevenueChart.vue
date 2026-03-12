<template>
  <div style="position: relative; height: 220px;">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps<{
  data: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor?: string
      backgroundColor?: string
      borderWidth?: number
      tension?: number
      fill?: boolean
    }[]
  }
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

onMounted(() => {
  if (!chartCanvas.value) return

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(10, 22, 40, 0.95)',
          borderColor: 'rgba(37, 99, 235, 0.4)',
          borderWidth: 1,
          titleColor: '#F1F5F9',
          bodyColor: '#94A3B8',
          padding: 10,
          callbacks: {
            label: (context) =>
              ` ₡${new Intl.NumberFormat('es-CR').format(context.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(37, 99, 235, 0.06)',
          },
          ticks: {
            color: '#64748B',
            font: { size: 11, family: 'Inter, sans-serif' },
          },
        },
        y: {
          grid: {
            color: 'rgba(37, 99, 235, 0.06)',
          },
          ticks: {
            color: '#64748B',
            font: { size: 11, family: 'Inter, sans-serif' },
            callback: (value) => `₡${Number(value).toLocaleString('es-CR')}`,
          },
        },
      },
      interaction: {
        intersect: false,
        mode: 'index',
      },
    },
  })
})

onBeforeUnmount(() => {
  chartInstance?.destroy()
})

watch(() => props.data, (newData) => {
  if (chartInstance) {
    chartInstance.data = newData
    chartInstance.update()
  }
})
</script>
