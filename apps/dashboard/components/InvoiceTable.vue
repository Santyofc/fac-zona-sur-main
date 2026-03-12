<template>
  <div>
    <div v-if="loading" style="padding: 2rem; text-align: center; color: var(--fcr-text-muted);">
      Cargando facturas...
    </div>
    <div v-else-if="!invoices.length" style="padding: 3rem; text-align: center; color: var(--fcr-text-muted);">
      <div style="font-size: 2rem; margin-bottom: 0.5rem;">📄</div>
      <div style="font-weight: 600;">No hay facturas</div>
      <div style="font-size: 0.85rem; margin-top: 0.25rem;">Crea tu primera factura electrónica</div>
    </div>
    <div v-else class="fcr-table-wrapper">
      <table class="fcr-table">
        <thead>
          <tr>
            <th>Consecutivo</th>
            <th v-if="!compact">Clave</th>
            <th>Cliente</th>
            <th>Fecha</th>
            <th>Total</th>
            <th>Estado</th>
            <th v-if="!compact">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in invoices" :key="inv.id">
            <td>
              <span style="font-family: monospace; font-size: 0.8rem; color: var(--fcr-blue-light);">
                {{ inv.consecutive }}
              </span>
            </td>
            <td v-if="!compact">
              <span style="font-family: monospace; font-size: 0.7rem; color: var(--fcr-text-muted);">
                {{ inv.clave ? inv.clave.substring(0, 20) + '...' : '—' }}
              </span>
            </td>
            <td style="font-weight: 500; color: var(--fcr-text-primary);">
              {{ inv.client_name || inv.client?.name || 'Consumidor Final' }}
            </td>
            <td style="font-size: 0.8rem;">{{ formatDate(inv.issue_date) }}</td>
            <td style="font-weight: 600; color: var(--fcr-text-primary);">
              {{ formatCurrency(inv.total, inv.currency) }}
            </td>
            <td>
              <span :class="`fcr-badge badge-${inv.status}`">
                {{ statusLabel(inv.status) }}
              </span>
            </td>
            <td v-if="!compact">
              <div style="display: flex; gap: 0.5rem;">
                <NuxtLink :to="`/invoices/${inv.id}`">
                  <button class="fcr-btn fcr-btn-ghost" style="padding: 0.25rem 0.625rem; font-size: 0.75rem;">
                    Ver
                  </button>
                </NuxtLink>
                <button v-if="inv.status === 'draft'"
                  class="fcr-btn fcr-btn-primary"
                  style="padding: 0.25rem 0.625rem; font-size: 0.75rem;"
                  @click="$emit('send', inv.id)">
                  Enviar
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

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('es-CR', { day: '2-digit', month: 'short', year: 'numeric' })

const formatCurrency = (v: number | string, currency = 'CRC') =>
  new Intl.NumberFormat('es-CR', {
    style: 'currency', currency,
    minimumFractionDigits: 0
  }).format(Number(v))
</script>
