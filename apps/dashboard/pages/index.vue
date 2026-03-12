<template>
  <div layout="default">
    <NuxtLayout>
      <h1 class="fcr-page-title">Dashboard</h1>
      <p class="fcr-page-subtitle">Resumen financiero del mes en curso</p>

      <!-- Stats Cards -->
      <StatsCards :stats="stats" :loading="statsLoading" />

      <!-- Charts + Quick Actions -->
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; margin-top: 1.5rem;">
        <!-- Revenue Chart -->
        <div class="fcr-card">
          <h2 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">Ingresos del Mes</h2>
          <RevenueChart :data="revenueData" />
        </div>

        <!-- Quick Stats -->
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          <div class="fcr-card">
            <div style="font-size: 0.75rem; color: var(--fcr-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: .05em;">Estado de Facturas</div>
            <div style="margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem;">
              <div v-for="item in statusBreakdown" :key="item.label"
                style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.8rem; color: var(--fcr-text-secondary);">{{ item.label }}</span>
                <span :class="`fcr-badge badge-${item.key}`">{{ item.count }}</span>
              </div>
            </div>
          </div>

          <div class="fcr-card fcr-glow">
            <div style="font-size: 0.75rem; color: var(--fcr-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: .05em;">IVA Acumulado</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #10B981; margin-top: 0.5rem;">
              {{ formatCRC(stats?.tax_accumulated || 0) }}
            </div>
            <div style="font-size: 0.75rem; color: var(--fcr-text-muted); margin-top: 0.25rem;">↑ Este mes</div>
          </div>
        </div>
      </div>

      <!-- Recent Invoices -->
      <div class="fcr-card" style="margin-top: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h2 style="font-size: 1rem; font-weight: 600;">Facturas Recientes</h2>
          <NuxtLink to="/invoices" style="font-size: 0.8rem; color: var(--fcr-blue-light);">Ver todas →</NuxtLink>
        </div>
        <InvoiceTable :invoices="recentInvoices" :loading="invoicesLoading" :compact="true" />
      </div>
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
import type { DashboardStats, Invoice } from '~/types'

const { fetchStats, fetchInvoices } = useInvoices()
const { formatCRC } = useFormatters()

const stats = ref<DashboardStats | null>(null)
const statsLoading = ref(true)
const recentInvoices = ref<Invoice[]>([])
const invoicesLoading = ref(true)

// Mock revenue data for chart (replace with API data)
const revenueData = ref({
  labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
  datasets: [{
    label: 'Ingresos (₡)',
    data: [850000, 1200000, 980000, 1450000],
    borderColor: '#2563EB',
    backgroundColor: 'rgba(37, 99, 235, 0.1)',
    borderWidth: 2,
    tension: 0.4,
    fill: true,
  }]
})

const statusBreakdown = computed(() => [
  { label: 'Aceptadas', key: 'accepted', count: stats.value?.invoices_accepted || 0 },
  { label: 'Pendientes', key: 'processing', count: stats.value?.invoices_pending || 0 },
  { label: 'Rechazadas', key: 'rejected', count: stats.value?.invoices_rejected || 0 },
])

// Formatters composable (inline)
function useFormatters() {
  const formatCRC = (value: number | string) => {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return new Intl.NumberFormat('es-CR', {
      style: 'currency', currency: 'CRC', minimumFractionDigits: 0
    }).format(num)
  }
  return { formatCRC }
}

onMounted(async () => {
  try {
    const [statsData, invoicesData] = await Promise.all([
      fetchStats(),
      fetchInvoices({ limit: 5 }),
    ])
    stats.value = statsData
    recentInvoices.value = invoicesData
  } catch (e) {
    console.error('Error loading dashboard:', e)
  } finally {
    statsLoading.value = false
    invoicesLoading.value = false
  }
})

useHead({ title: 'Dashboard — Factura CR' })
</script>
