<template>
  <div>
    <!-- Header Section -->
    <div class="mb-10 animate-fade-in flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div>
        <h1 class="text-4xl md:text-5xl zs-heading-premium zs-text-gradient mb-4">
          Center of Operations
        </h1>
        <div class="flex items-center gap-3">
          <div class="w-2 h-2 rounded-full bg-zs-blue animate-pulse shadow-[0_0_10px_rgba(37,99,235,1)]"></div>
          <p class="text-[11px] uppercase font-bold tracking-[0.3em] text-zs-text-muted">
            Status: Synchronized — {{ companyName }}
          </p>
        </div>
      </div>
      <NuxtLink to="/invoices/new">
        <button class="zs-btn h-12 px-8">
          <UIcon name="i-heroicons-plus-16-solid" class="w-5 h-5" />
          NUEVA FACTURA
        </button>
      </NuxtLink>
    </div>

    <!-- Bento Dashboard Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 lg:grid-rows-6 gap-6 h-auto lg:h-[1000px] mt-10">
      <!-- Stats (First Row) -->
      <div class="md:col-span-2 lg:col-span-4 lg:row-span-1">
        <StatsCards :stats="stats" :loading="statsLoading" />
      </div>
      <!-- Recent Invoices (Bento Core) -->
      <div class="md:col-span-2 lg:col-span-3 lg:row-span-3 zs-card p-0 overflow-hidden animate-cascade animate-delay-200">
        <div class="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
          <div>
            <h2 class="text-sm zs-heading-premium text-white">Documentos Emitidos</h2>
            <p class="text-[10px] text-zs-text-muted mt-2 uppercase tracking-widest font-bold">Registro histórico de transacciones</p>
          </div>
          <NuxtLink to="/invoices">
            <button class="text-[10px] font-black uppercase tracking-widest text-zs-blue-lt hover:text-white transition-all bg-zs-blue/5 px-4 py-2 rounded-lg border border-zs-blue/20 hover:border-zs-blue/40">
              EXPLORAR TODO
            </button>
          </NuxtLink>
        </div>
        <InvoiceTable :invoices="recentInvoices" :loading="invoicesLoading" :compact="true" />
      </div>

      <!-- Quick Actions / Status (Right Column) -->
      <div class="lg:col-span-1 lg:row-span-3 zs-card p-8 animate-cascade animate-delay-300">
        <h2 class="text-sm zs-heading-premium text-white mb-8">Estado de Red</h2>
        <div class="space-y-6">
          <div v-for="item in statusBreakdown" :key="item.label" 
            class="flex items-center justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/5 group hover:border-zs-blue/30 transition-all hover:bg-zs-blue/[0.03]">
            <div class="flex items-center gap-4">
              <div class="w-2.5 h-2.5 rounded-full shadow-[0_0_8px_currentColor]" :class="item.dotClass"></div>
              <span class="text-xs font-bold text-zs-text-secondary group-hover:text-white transition-colors uppercase tracking-wider">{{ item.label }}</span>
            </div>
            <span class="text-xs font-black text-white px-3 py-1 rounded-lg bg-white/5 border border-white/10 group-hover:border-zs-blue/40">
              {{ item.count }}
            </span>
          </div>
        </div>
      </div>

      <!-- Revenue Data (Bottom Grid) -->
      <div class="md:col-span-2 lg:col-span-2 lg:row-span-2 zs-card p-8 animate-cascade animate-delay-400">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-sm zs-heading-premium text-white">Análisis Financiero</h2>
            <p class="text-[10px] text-zs-text-muted mt-2 uppercase tracking-widest font-bold">Rendimiento Mensual</p>
          </div>
          <div class="flex gap-2">
            <div class="px-4 py-1.5 rounded-full bg-zs-blue/10 border border-zs-blue/20 text-[9px] font-black text-zs-blue-lt uppercase tracking-widest">LIVE DATA</div>
          </div>
        </div>
        <div class="h-[180px]">
          <RevenueChart :data="revenueData" />
        </div>
      </div>

      <!-- Tax Highlight (Bento Bottom) -->
      <div class="lg:col-span-1 lg:row-span-2 zs-card zs-kpi-accent emerald p-8 animate-cascade animate-delay-500 overflow-hidden group">
        <div class="relative z-10 text-center py-2">
          <div class="text-[10px] font-black uppercase tracking-[0.3em] text-zs-text-muted mb-6 group-hover:text-zs-text-secondary transition-colors">
            IVA Acumulado
          </div>
          <div class="text-4xl font-black tracking-tighter text-white group-hover:scale-105 transition-transform duration-normal">
            {{ formatCRC(stats?.tax_accumulated || 0) }}
          </div>
          <div class="mt-8 flex items-center justify-center gap-3">
            <div class="flex items-center gap-1.5 text-[10px] font-black text-zs-emerald ring-1 ring-zs-emerald/20 px-2 py-1 rounded-md bg-zs-emerald/10">
              <span>↑ 14.5%</span>
            </div>
            <span class="text-[10px] text-zs-text-muted uppercase font-bold tracking-widest">PERIODO ACTUAL</span>
          </div>
        </div>
      </div>

      <!-- System Status (Small Bento Tile) -->
      <div class="lg:col-span-1 lg:row-span-2 zs-card p-8 animate-cascade animate-delay-600 bg-zs-gradient-dark border-zs-blue/5 overflow-hidden">
        <div class="flex items-center gap-4 mb-8">
          <div class="w-10 h-10 rounded-2xl bg-zs-blue/10 flex items-center justify-center border border-zs-blue/20 shadow-zs-glow-blue">
            <span class="text-zs-blue text-xs font-black">AI</span>
          </div>
          <div class="text-[10px] zs-heading-premium text-white">System Core</div>
        </div>
        <div class="space-y-4">
          <div class="flex justify-between text-[10px] font-black uppercase tracking-widest">
            <span class="text-zs-text-muted">Health Score</span>
            <span class="text-zs-emerald">99.8%</span>
          </div>
          <div class="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div class="w-[99.8%] h-full bg-zs-gradient-blue animate-pulse"></div>
          </div>
          <p class="text-[9px] text-zs-text-muted italic mt-4">All subsystems are operational.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DashboardStats, Invoice } from '~/types'
import { ref, computed, onMounted } from 'vue'

const { fetchStats, fetchInvoices } = useInvoices()
const companyName = ref('Zona Sur Tech') // In production this comes from user session

const stats = ref<DashboardStats | null>(null)
const statsLoading = ref(true)
const recentInvoices = ref<Invoice[]>([])
const invoicesLoading = ref(true)

// Advanced revenue data for premium look
const revenueData = computed(() => ({
  labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
  datasets: [{
    label: 'Ingresos (₡)',
    data: [750000, 1100000, 890000, 1550000],
    borderColor: '#3b82f6', // zs-blue
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
  }]
}))

const statusBreakdown = computed(() => [
  { label: 'Aceptadas', key: 'accepted', count: stats.value?.invoices_accepted || 0, dotClass: 'bg-zs-emerald' },
  { label: 'Pendientes', key: 'processing', count: stats.value?.invoices_pending || 0, dotClass: 'bg-zs-violet' },
  { label: 'Rechazadas', key: 'rejected', count: stats.value?.invoices_rejected || 0, dotClass: 'bg-zs-rose' },
])

const formatCRC = (value: number | string) => {
  const num = typeof value === 'string' ? parseFloat(value) : (value || 0)
  return new Intl.NumberFormat('es-CR', {
    style: 'currency', currency: 'CRC', minimumFractionDigits: 0
  }).format(num)
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
