<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full h-full">
    <div v-for="card in cards" :key="card.key" class="zs-card zs-kpi-accent p-8 group flex flex-col justify-between" :class="card.accentClass">
      <div class="flex justify-between items-start">
        <div>
          <div class="text-[10px] font-black uppercase tracking-[0.2em] text-zs-text-muted mb-2 group-hover:text-zs-text-secondary transition-colors">
            {{ card.label }}
          </div>
          <div class="text-3xl font-black tracking-tighter text-white group-hover:scale-110 group-hover:zs-text-gradient transition-all duration-normal origin-left">
            <template v-if="loading">
              <div class="h-10 w-32 bg-white/10 rounded-xl animate-pulse"></div>
            </template>
            <template v-else>{{ card.formatted }}</template>
          </div>
          <div v-if="card.change !== null" class="flex items-center gap-1.5 mt-3">
            <div class="flex items-center gap-0.5 text-[10px] font-bold" :class="card.change > 0 ? 'text-zs-emerald' : 'text-zs-rose'">
              <span v-if="card.change > 0">↑</span>
              <span v-else>↓</span>
              {{ Math.abs(card.change) }}%
            </div>
            <span class="text-[10px] text-zs-text-muted font-medium uppercase tracking-wider">vs mes anterior</span>
          </div>
        </div>
        
        <div class="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:border-white/20 transition-all duration-normal shadow-zs-card">
          <component :is="card.icon" class="w-6 h-6 transition-colors duration-normal" :class="card.iconClass" />
        </div>
      </div>

      <!-- Detail visualization (small graph placeholder) -->
      <div class="mt-6 flex items-end gap-1 h-3 opacity-20 group-hover:opacity-40 transition-opacity">
        <div v-for="i in 12" :key="i" class="flex-1 bg-current rounded-full" 
          :class="card.iconClass"
          :style="{ height: `${Math.random() * 100}%` }"></div>
      </div>

      <!-- Accent glow (hover) -->
      <div class="absolute -bottom-10 -right-10 w-24 h-24 rounded-full blur-[40px] opacity-0 group-hover:opacity-20 transition-opacity" :class="card.bgClass"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent } from 'vue'

// Inline Heroicons for better portability
const CurrencyDollarIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>`
})
const DocumentTextIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>`
})
const ReceiptPercentIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 0 0-3.7-3.7 48.678 48.678 0 0 0-7.324 0 4.006 4.006 0 0 0-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 0 0 3.7 3.7 48.656 48.656 0 0 0 7.324 0 4.006 4.006 0 0 0 3.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3-3 3" /></svg>`
})
const ClockIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>`
})

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
    icon: CurrencyDollarIcon,
    accentClass: 'blue',
    iconClass: 'text-zs-blue-lt',
    bgClass: 'bg-zs-blue',
    change: 12.4,
  },
  {
    key: 'invoices',
    label: 'Facturas Emitidas',
    formatted: String(props.stats?.invoices_issued || 0),
    icon: DocumentTextIcon,
    accentClass: 'cyan',
    iconClass: 'text-zs-cyan',
    bgClass: 'bg-zs-cyan',
    change: 8.1,
  },
  {
    key: 'tax',
    label: 'IVA Acumulado',
    formatted: fmt(props.stats?.tax_accumulated || 0),
    icon: ReceiptPercentIcon,
    accentClass: 'emerald',
    iconClass: 'text-zs-emerald',
    bgClass: 'bg-zs-emerald',
    change: null,
  },
  {
    key: 'pending',
    label: 'Facturas Pendientes',
    formatted: String(props.stats?.invoices_pending || 0),
    icon: ClockIcon,
    accentClass: 'violet',
    iconClass: 'text-zs-violet',
    bgClass: 'bg-zs-violet',
    change: null,
  },
])
</script>
