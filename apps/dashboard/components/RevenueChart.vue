<template>
  <div class="relative h-[240px] w-full p-2">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
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

  // Update data styling for premium look
  const styledData = {
    ...props.data,
    datasets: props.data.datasets.map(ds => ({
      ...ds,
      borderColor: ds.borderColor || '#3b82f6', // zs-blue
      backgroundColor: ds.backgroundColor || 'rgba(59, 130, 246, 0.05)',
      borderWidth: 4,
      pointRadius: 0,
      pointHoverRadius: 8,
      pointHoverBackgroundColor: '#3b82f6',
      pointHoverBorderWidth: 4,
      pointHoverBorderColor: 'rgba(255, 255, 255, 0.1)',
      tension: 0.5,
      fill: 'start'
    }))
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: styledData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: '#0a0d18',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          titleFont: { weight: 'bold', size: 12 },
          bodyColor: '#94a3b8',
          bodyFont: { size: 11 },
          padding: 12,
          displayColors: false,
          cornerRadius: 12,
          callbacks: {
            label: (context) => 
              ` ₡${new Intl.NumberFormat('es-CR').format(context.parsed.y)}`
          },
        },
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#475569',
            font: { size: 10, family: 'Inter, sans-serif' },
            padding: 10
          },
        },
        y: {
          grid: {
            color: 'rgba(255, 255, 255, 0.03)',
          },
          border: { dash: [4, 4], display: false },
          ticks: {
            color: '#475569',
            font: { size: 10, family: 'Inter, sans-serif' },
            padding: 10,
            callback: (value: number | string) => {
              const num = Number(value)
              return num >= 1000 ? (num/1000) + 'k' : num.toString()
            },
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
    chartInstance.data = {
      ...newData,
      datasets: newData.datasets.map(ds => ({
        ...ds,
        borderColor: ds.borderColor || '#3b82f6',
        borderWidth: 4,
        pointRadius: 0,
        tension: 0.5,
      }))
    }
    chartInstance.update()
  }
}, { deep: true })
</script>
