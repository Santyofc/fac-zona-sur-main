<template>
  <div class="p-8 max-w-7xl mx-auto space-y-12 pb-24">
    <!-- Header -->
    <header class="flex flex-col md:flex-row md:items-end justify-between gap-8 animate-zs-fade-up">
      <div class="space-y-4">
        <h1 class="text-5xl font-black uppercase tracking-tighter italic text-white italic">
          Centro de <span class="zs-text-gradient">Control Digital</span>
        </h1>
        <div class="flex items-center gap-4">
          <span class="zs-badge-status zs-badge-accepted">Hacienda v4.4 • Conectado</span>
          <p class="text-[10px] font-black uppercase tracking-[0.3em] text-zs-text-muted">
            Última Sincronización: 21 Mar 2026 • 09:14:22
          </p>
        </div>
      </div>
      <div class="flex gap-4">
        <button class="zs-btn-ghost px-6 h-12">
          <UIcon name="i-heroicons-arrow-path" class="w-4 h-4" />
          REFRESCAR
        </button>
        <button class="zs-btn px-6 h-12">
          <UIcon name="i-heroicons-plus-16-solid" class="w-5 h-5" />
          NUEVA FACTURA
        </button>
      </div>
    </header>

    <!-- KPI Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-cascade">
      <PremiumMetric 
        label="Ingresos del Mes" 
        value="₡1,245,800"
        accent="blue"
        trend="12.5"
        icon="i-heroicons-currency-dollar" 
      />
      <PremiumMetric 
        label="Facturas Emitidas" 
        value="87"
        accent="violet"
        trend="8.1"
        icon="i-heroicons-document-text" 
      />
      <PremiumMetric 
        label="IVA Acumulado" 
        value="₡161,954"
        accent="emerald"
        trend="4.2"
        icon="i-heroicons-receipt-percent" 
      />
      <PremiumMetric 
        label="Pendientes Hacienda" 
        value="3"
        accent="amber"
        trend="-2.4"
        icon="i-heroicons-clock" 
      />
    </div>

    <!-- Main Content Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Recent Documents -->
      <section class="lg:col-span-2 zs-card p-0 animate-zs-fade-up" style="animation-delay: 0.4s">
        <div class="p-8 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-sm zs-heading-premium text-white">Documentos Recientes</h2>
          <button class="text-[10px] font-black uppercase tracking-widest text-zs-blue-lt hover:text-white transition-all">
            VER REPORTE COMPLETO →
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="zs-table">
            <thead>
              <tr>
                <th>Documento</th>
                <th>Receptor</th>
                <th>Monto</th>
                <th>Estado Hacienda</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in recentInvoices" :key="inv.id">
                <td class="font-mono text-[11px] text-zs-blue-lt">{{ inv.number }}</td>
                <td>
                  <div class="flex flex-col">
                    <span class="text-white font-bold">{{ inv.client }}</span>
                    <span class="text-[10px] text-zs-text-muted">{{ inv.idNumber }}</span>
                  </div>
                </td>
                <td class="font-mono text-white">{{ inv.amount }}</td>
                <td>
                  <span class="zs-badge-status" :class="inv.statusClass">{{ inv.status }}</span>
                </td>
                <td>
                  <div class="flex gap-2">
                    <button class="p-2 rounded-lg bg-white/5 border border-white/10 hover:border-zs-blue/40 transition-all">
                      <UIcon name="i-heroicons-document-arrow-down" class="w-4 h-4 text-zs-text-secondary" />
                    </button>
                    <button class="p-2 rounded-lg bg-white/5 border border-white/10 hover:border-zs-blue/40 transition-all">
                      <UIcon name="i-heroicons-envelope" class="w-4 h-4 text-zs-text-secondary" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Sidebar Status -->
      <aside class="space-y-8 animate-zs-fade-up" style="animation-delay: 0.5s">
        <!-- Hacienda Timeline -->
        <div class="zs-card p-8">
          <h2 class="text-sm zs-heading-premium text-white mb-8 italic">Transmisión en tiempo real</h2>
          <StatusTimeline :steps="timelineSteps" />
        </div>

        <!-- System Health -->
        <div class="zs-card p-8 bg-zs-gradient-blue border-none overflow-hidden relative group">
          <div class="relative z-10">
            <h2 class="text-[10px] font-black uppercase tracking-[0.2em] text-white/60 mb-6 italic">Infraestructura</h2>
            <div class="flex items-center justify-between mb-4">
              <span class="text-2xl font-black text-white italic tracking-tighter">99.98%</span>
              <span class="text-[9px] font-black bg-white/20 text-white px-2 py-1 rounded-md">OPERATIONAL</span>
            </div>
            <div class="w-full h-1 bg-white/10 rounded-full overflow-hidden">
              <div class="w-[99.98%] h-full bg-white animate-pulse"></div>
            </div>
          </div>
          <!-- Decorative SVG Grid -->
          <div class="absolute inset-0 opacity-10 pointer-events-none group-hover:opacity-20 transition-opacity">
            <svg class="w-full h-full" viewBox="0 0 100 100">
              <defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="white" stroke-width="0.5"/></pattern></defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TimelineStep } from '~/components/ui/StatusTimeline.vue'

const recentInvoices = [
  { id: 1, number: 'FE-0010000000087', client: 'Supermercado La Colonia', idNumber: '3-101-854120', amount: '₡325,800', status: 'Aceptada', statusClass: 'zs-badge-accepted' },
  { id: 2, number: 'FE-0010000000086', client: 'Constructora Del Sur', idNumber: '3-101-720430', amount: '₡1,240,000', status: 'Pendiente', statusClass: 'zs-badge-pending' },
  { id: 3, number: 'FE-0010000000085', client: 'Carlos Méndez Vega', idNumber: '1-0845-0234', amount: '₡45,000', status: 'Aceptada', statusClass: 'zs-badge-accepted' },
  { id: 4, number: 'FE-0010000000084', client: 'Clínica Santa Elena', idNumber: '3-101-625890', amount: '₡98,500', status: 'Rechazada', statusClass: 'zs-badge-rejected' },
]

const timelineSteps: TimelineStep[] = [
  { title: 'Factura Recibida', description: 'Borrador generado con consecutivo FE-88 asignado.', time: '09:14:22', status: 'done' },
  { title: 'XML v4.4 Generado', description: 'Comprobante estructurado según esquema Hacienda.', time: '09:14:23', status: 'done', code: 'FE_00000088_210326.xml' },
  { title: 'Firma Digital Aplicada', description: 'XAdES-BES firmada con certificado BCCR.', time: '09:14:24', status: 'done' },
  { title: 'Enviando a Hacienda', description: 'Posteando documento a Recepción API.', time: '09:14:26', status: 'active' },
  { title: 'Respuesta Recibida', description: 'Esperando validación fiscal externa.', time: '-', status: 'pending' },
]

useHead({ title: 'Premium Preview — Factura CR' })
</script>

<style>
/* Nuxt Head Background Override for Demo */
body {
  background-color: var(--zs-bg-primary) !important;
}
</style>
