<template>
  <div class="fcr-grid-4">
    <div v-for="card in cards" :key="card.key" class="fcr-card" style="position: relative; overflow: hidden;">
      <!-- Background glow accent -->
      <div :style="`position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; border-radius: 50%; background: ${card.color}; opacity: 0.12; filter: blur(20px);`"></div>

      <div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative;">
        <div>
          <div class="fcr-stat-label">{{ card.label }}</div>
          <div class="fcr-stat-value" style="margin-top: 0.375rem;">
            <template v-if="loading">
              <div style="height: 28px; width: 120px; background: var(--fcr-bg-secondary); border-radius: 6px; animation: pulse 1.5s ease-in-out infinite;"></div>
            </template>
            <template v-else>{{ card.formatted }}</template>
          </div>
          <div v-if="card.change" style="font-size: 0.75rem; margin-top: 0.375rem;" :style="{ color: card.change > 0 ? '#10B981' : '#EF4444' }">
            {{ card.change > 0 ? '↑' : '↓' }} {{ Math.abs(card.change) }}% vs mes anterior
          </div>
        </div>
        <div class="fcr-stat-icon" :style="`background: ${card.bg}`">
          <span style="font-size: 1.1rem;">{{ card.icon }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface DashboardStats {
  revenue_month: number
  invoices_issued: number
  tax_accumulated: number
  invoices_pending: number
}

const props = defineProps<{
  stats: DashboardStats | null
  loading?: boolean
}>()

const fmt = (v: number) => new Intl.NumberFormat('es-CR', {
  style: 'currency', currency: 'CRC', minimumFractionDigits: 0
}).format(v)

const cards = computed(() => [
  {
    key: 'revenue',
    label: 'Ingresos del Mes',
    formatted: fmt(props.stats?.revenue_month || 0),
    icon: '💰',
    color: '#3B82F6',
    bg: 'rgba(59, 130, 246, 0.15)',
    change: 12.4,
  },
  {
    key: 'invoices',
    label: 'Facturas Emitidas',
    formatted: String(props.stats?.invoices_issued || 0),
    icon: '📄',
    color: '#06B6D4',
    bg: 'rgba(6, 182, 212, 0.15)',
    change: 8.1,
  },
  {
    key: 'tax',
    label: 'IVA Acumulado',
    formatted: fmt(props.stats?.tax_accumulated || 0),
    icon: '🧾',
    color: '#10B981',
    bg: 'rgba(16, 185, 129, 0.15)',
    change: null,
  },
  {
    key: 'pending',
    label: 'Facturas Pendientes',
    formatted: String(props.stats?.invoices_pending || 0),
    icon: '⏳',
    color: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.15)',
    change: null,
  },
])
</script>

<style scoped>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
