<template>
  <div class="zs-card overflow-hidden">
    <div v-if="loading" class="p-20 text-center space-y-4">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zs-blue/10 border border-zs-blue/20 animate-pulse">
        <ArrowPathIcon class="w-8 h-8 text-zs-blue animate-spin" />
      </div>
      <div class="text-xs font-black uppercase tracking-[0.2em] text-zs-text-muted">Sincronizando Facturas...</div>
    </div>

    <div v-else-if="!invoices.length" class="p-20 text-center space-y-4">
      <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-normal">
        <DocumentIcon class="w-10 h-10 text-zs-text-muted opacity-50" />
      </div>
      <div>
        <div class="text-lg font-black text-white tracking-tight">Registro Vacío</div>
        <div class="text-xs text-zs-text-muted uppercase tracking-[0.1em] mt-1">No se detectaron transacciones emitidas</div>
      </div>
      <NuxtLink to="/invoices/new" class="inline-block pt-4">
        <button class="zs-btn secondary">EMITIR PRIMERA FACTURA</button>
      </NuxtLink>
    </div>

    <div v-else class="overflow-x-auto no-scrollbar">
      <table class="zs-table border-separate border-spacing-y-2 px-6">
        <thead>
          <tr class="text-zs-text-muted">
            <th class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4">Consecutivo</th>
            <th v-if="!compact" class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4">Clave Acceso</th>
            <th class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4 text-left">Cliente Receptor</th>
            <th class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4">Emisión</th>
            <th class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4">Monto Total</th>
            <th class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4">Estado</th>
            <th v-if="!compact" class="pb-4 font-black text-[10px] uppercase tracking-[0.2em] px-4 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="before:content-['-'] before:block before:leading-[1px] before:text-transparent">
          <tr v-for="inv in invoices" :key="inv.id" class="group/row cursor-pointer transition-all duration-normal hover:translate-x-1">
            <td class="bg-white/5 backdrop-blur-md rounded-l-2xl border-y border-l border-white/5 py-4 px-4">
              <div class="flex flex-col">
                <span class="font-mono text-[11px] text-zs-blue-lt font-bold tracking-wider">
                  {{ inv.consecutive }}
                </span>
                <span class="text-[9px] uppercase tracking-tighter text-zs-text-muted">Digital Asset</span>
              </div>
            </td>
            <td v-if="!compact">
              <span class="font-mono text-[10px] text-zs-text-muted truncate block max-w-[120px] opacity-60 group-hover/row:opacity-100 transition-opacity">
                {{ inv.clave || '—' }}
              </span>
            </td>
            <td>
              <div class="text-sm font-bold text-white group-hover/row:text-zs-blue transition-colors">
                {{ inv.client_name || inv.client?.name || 'CONSUMIDOR FINAL' }}
              </div>
            </td>
            <td>
                <span class="text-xs font-bold text-zs-text-secondary">
                  {{ formatDate(inv.issue_date) }}
                </span>
              </td>
              <td class="bg-white/5 backdrop-blur-md border-y border-white/5 py-4 px-4">
                <div class="text-sm font-black text-white tracking-tight">
                  <span class="text-xs opacity-50 mr-1">{{ inv.currency === 'USD' ? '$' : '₡' }}</span>
                  {{ formatCurrencyAmount(inv.total) }}
                </div>
              </td>
              <td class="bg-white/5 backdrop-blur-md border-y border-white/5 py-4 px-4">
                <span :class="badgeClass(inv.status)" class="text-[9px] uppercase font-black tracking-widest py-1.5 px-4 rounded-full border">
                  {{ statusLabel(inv.status) }}
                </span>
              </td>
              <td v-if="!compact" class="bg-white/5 backdrop-blur-md rounded-r-2xl border-y border-r border-white/5 py-4 px-4 text-right">
              <div class="flex items-center justify-end gap-2 opacity-0 group-hover/row:opacity-100 transition-opacity">
                <NuxtLink :to="`/invoices/${inv.id}`">
                  <button class="p-2 rounded-lg hover:bg-white/10 text-zs-text-muted hover:text-white transition-all">
                    <EyeIcon class="w-4 h-4" />
                  </button>
                </NuxtLink>
                <button v-if="inv.status === 'draft'"
                  class="p-2 rounded-lg hover:bg-zs-blue/20 text-zs-blue hover:text-zs-blue-lt transition-all"
                  @click.stop="$emit('send', inv.id)">
                  <PaperAirplaneIcon class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// Inline Icons
const ArrowPathIcon = defineComponent({ template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>` })
const DocumentIcon = defineComponent({ template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>` })
const EyeIcon = defineComponent({ template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>` })
const PaperAirplaneIcon = defineComponent({ template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" /></svg>` })

interface Invoice {
  id: string
  consecutive: string
  clave?: string
  client_name?: string
  client?: { name: string }
  issue_date: string
  total: number | string
  currency: string
  status: string
}

const props = defineProps<{
  invoices: Invoice[]
  loading?: boolean
  compact?: boolean
}>()

defineEmits<{
  (e: 'send', id: string): void
}>()

const statusLabels: Record<string, string> = {
  draft: 'Borrador',
  processing: 'Procesando',
  sent: 'Enviada',
  accepted: 'Aceptada',
  rejected: 'Rechazada',
  cancelled: 'Cancelada',
}

const statusLabel = (s: string) => statusLabels[s] || s

const badgeClass = (status: string) => {
  const base = 'transition-all duration-normal border-opacity-20 '
  switch (status) {
    case 'accepted': return base + 'bg-zs-emerald/10 text-zs-emerald border-zs-emerald shadow-zs-glow-emerald/20'
    case 'rejected':
    case 'cancelled': return base + 'bg-zs-rose/10 text-zs-rose border-zs-rose shadow-zs-glow-rose/20'
    case 'processing': return base + 'bg-zs-violet/10 text-zs-violet border-zs-violet animate-pulse'
    case 'sent': return base + 'bg-zs-cyan/10 text-zs-cyan border-zs-cyan shadow-zs-glow-blue/20'
    default: return base + 'bg-white/5 text-zs-text-muted border-white/10'
  }
}

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('es-CR', { day: '2-digit', month: 'short', year: 'numeric' })

const formatCurrencyAmount = (v: number | string) =>
  new Intl.NumberFormat('es-CR', {
    minimumFractionDigits: 0
  }).format(Number(v))
</script>
