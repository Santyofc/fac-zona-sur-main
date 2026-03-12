<template>
  <NuxtLayout>
    <h1 class="fcr-page-title">Reportes</h1>
    <p class="fcr-page-subtitle">Análisis financiero y detalle de IVA para Hacienda</p>

    <!-- Period selector -->
    <div class="fcr-card" style="margin-bottom: 1rem; display: flex; gap: 1rem; align-items: center;">
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <label class="fcr-label" style="margin: 0;">Período:</label>
        <select v-model="period" class="fcr-input" style="max-width: 160px; cursor: pointer;" @change="loadData">
          <option value="month">Este mes</option>
          <option value="last_month">Mes anterior</option>
          <option value="quarter">Este trimestre</option>
          <option value="year">Este año</option>
        </select>
      </div>
    </div>

    <!-- Summary cards -->
    <div class="fcr-grid-4" style="margin-bottom: 1rem;">
      <div v-for="card in summaryCards" :key="card.label" class="fcr-card">
        <div class="fcr-stat-label">{{ card.label }}</div>
        <div class="fcr-stat-value" style="margin-top: 0.375rem;">{{ card.value }}</div>
      </div>
    </div>

    <!-- Charts row -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
      <!-- Monthly Trend -->
      <div class="fcr-card">
        <h2 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 1rem;">Ventas Mensuales</h2>
        <RevenueChart :data="monthlyChartData" />
      </div>
      <!-- IVA Breakdown -->
      <div class="fcr-card">
        <h2 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 1rem;">IVA por Tarifa</h2>
        <canvas ref="ivaChart" style="max-height: 220px;"></canvas>
      </div>
    </div>

    <!-- Invoice status table -->
    <div class="fcr-card">
      <h2 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 1rem;">Estado de Comprobantes</h2>
      <div class="fcr-table-wrapper">
        <table class="fcr-table">
          <thead><tr>
            <th>Estado</th><th>Cantidad</th><th>Monto Subtotal</th><th>IVA</th><th>Total</th>
          </tr></thead>
          <tbody>
            <tr v-for="row in statusReport" :key="row.status">
              <td><span :class="`fcr-badge badge-${row.status}`">{{ row.label }}</span></td>
              <td>{{ row.count }}</td>
              <td>{{ fmt(row.subtotal) }}</td>
              <td>{{ fmt(row.tax) }}</td>
              <td style="font-weight: 600;">{{ fmt(row.total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const { fetchInvoices } = useInvoices()

const period  = ref('month')
const invoices = ref([])
const ivaChart = ref<HTMLCanvasElement | null>(null)
let ivaChartInstance: any = null

const fmt = (v: number) => new Intl.NumberFormat('es-CR', {
  style: 'currency', currency: 'CRC', minimumFractionDigits: 0
}).format(Number(v) || 0)

// Estadísticas calculadas desde invoices
const summaryCards = computed(() => [
  { label: 'Facturas Emitidas', value: invoices.value.length },
  { label: 'Total Ventas Netas',  value: fmt(invoices.value.reduce((s: number, i: any) => s + Number(i.subtotal || 0), 0)) },
  { label: 'IVA Acumulado',       value: fmt(invoices.value.reduce((s: number, i: any) => s + Number(i.tax_total || 0), 0)) },
  { label: 'Total Cobrado',       value: fmt(invoices.value.filter((i: any) => i.status === 'accepted').reduce((s: number, i: any) => s + Number(i.total || 0), 0)) },
])

const monthlyChartData = computed(() => ({
  labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
  datasets: [{
    label: 'Ingresos (₡)',
    data: [
      group(0, 7), group(7, 14), group(14, 21), group(21, 31)
    ],
    borderColor: '#2563EB', backgroundColor: 'rgba(37,99,235,0.1)',
    borderWidth: 2, tension: 0.4, fill: true,
  }]
}))

function group(startDay: number, endDay: number): number {
  return invoices.value
    .filter((i: any) => {
      const d = new Date(i.issue_date || i.created_at)
      return d.getDate() > startDay && d.getDate() <= endDay
    })
    .reduce((s: number, i: any) => s + Number(i.total || 0), 0)
}

const statusReport = computed(() => {
  const statuses = ['accepted', 'sent', 'processing', 'draft', 'rejected', 'cancelled']
  const labels: Record<string, string> = {
    accepted: 'Aceptadas', sent: 'Enviadas', processing: 'Procesando',
    draft: 'Borrador', rejected: 'Rechazadas', cancelled: 'Canceladas',
  }
  return statuses.map(status => {
    const filtered = invoices.value.filter((i: any) => i.status === status)
    return {
      status, label: labels[status],
      count:    filtered.length,
      subtotal: filtered.reduce((s: number, i: any) => s + Number(i.subtotal || 0), 0),
      tax:      filtered.reduce((s: number, i: any) => s + Number(i.tax_total || 0), 0),
      total:    filtered.reduce((s: number, i: any) => s + Number(i.total || 0), 0),
    }
  }).filter(r => r.count > 0)
})

async function loadData() {
  invoices.value = await fetchInvoices({ limit: 200 })
  await nextTick()
  buildIvaChart()
}

function buildIvaChart() {
  if (ivaChartInstance) ivaChartInstance.destroy()
  if (!ivaChart.value) return

  const taxBrackets: Record<string, number> = { '13%': 0, '8%': 0, '4%': 0, '0%': 0 }
  // In a real app, sum by tax rate from items
  taxBrackets['13%'] = invoices.value
    .filter((i: any) => i.status === 'accepted')
    .reduce((s: number, i: any) => s + Number(i.tax_total || 0), 0)

  ivaChartInstance = new Chart(ivaChart.value, {
    type: 'doughnut',
    data: {
      labels: Object.keys(taxBrackets),
      datasets: [{
        data: Object.values(taxBrackets),
        backgroundColor: ['#2563EB', '#06B6D4', '#10B981', '#64748B'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right', labels: { color: '#94A3B8', font: { size: 11 } } } }
    }
  })
}

onMounted(loadData)
onBeforeUnmount(() => ivaChartInstance?.destroy())
useHead({ title: 'Reportes — Factura CR' })
</script>
