<template>
  <div class="space-y-8">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
      <div>
        <h1 class="text-3xl font-black zs-text-gradient tracking-tight mb-2 uppercase">
          Gestión de Documentos
        </h1>
        <div class="flex items-center gap-2">
          <div class="w-1.5 h-1.5 rounded-full bg-zs-blue animate-pulse"></div>
          <p class="text-[10px] uppercase font-bold tracking-[0.2em] text-zs-text-muted">
            Control Central de Facturación Electrónica
          </p>
        </div>
      </div>
      <NuxtLink to="/invoices/new" class="group">
        <button class="zs-btn-primary flex items-center gap-2 px-6 py-3">
          <span class="text-lg font-black">+</span>
          <span class="text-[11px] font-black tracking-[0.2em] uppercase">Nueva Factura</span>
        </button>
      </NuxtLink>
    </div>

    <!-- Filters & Search Bar -->
    <div class="zs-card p-4 flex flex-col md:flex-row gap-4 items-center bg-white/[0.02] border-white/5 animate-cascade animate-delay-100">
      <div class="relative flex-1 w-full">
        <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <svg class="w-4 h-4 text-zs-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input 
          v-model="search" 
          type="text" 
          class="w-full bg-black/20 border border-white/5 rounded-xl py-2.5 pl-10 pr-4 text-xs font-bold text-white placeholder:text-zs-text-muted focus:border-zs-blue/40 focus:ring-1 focus:ring-zs-blue/20 transition-all outline-none"
          placeholder="BUSCAR POR CLAVE, RECEPTOR O MONTO..." 
        />
      </div>
      
      <div class="flex items-center gap-3 w-full md:w-auto">
        <select 
          v-model="statusFilter" 
          class="flex-1 md:flex-none bg-black/20 border border-white/5 rounded-xl py-2.5 px-4 text-[10px] font-black uppercase tracking-widest text-zs-text-secondary cursor-pointer hover:border-white/10 transition-colors outline-none"
        >
          <option value="">TODOS LOS ESTADOS</option>
          <option value="draft">Borrador</option>
          <option value="processing">Procesando</option>
          <option value="accepted">Aceptada</option>
          <option value="rejected">Rechazada</option>
        </select>
        
        <button 
          @click="loadInvoices"
          class="p-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-zs-text-secondary transition-all group"
          title="Actualizar Lista"
        >
          <svg class="w-4 h-4 group-active:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Table Section -->
    <div class="zs-card p-0 overflow-hidden animate-cascade animate-delay-200">
      <div class="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
        <div>
          <h2 class="text-sm font-black uppercase tracking-[0.2em] text-white">Listado de Comprobantes</h2>
          <p class="text-[10px] text-zs-text-muted mt-1 uppercase">Historial completo sincronizado con el Ministerio de Hacienda</p>
        </div>
      </div>
      <InvoiceTable :invoices="invoices" :loading="loading" @send="handleSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const { fetchInvoices, sendInvoice } = useInvoices()
const invoices = ref([])
const loading = ref(true)
const search = ref('')
const statusFilter = ref('')

async function loadInvoices() {
  loading.value = true
  try {
    invoices.value = await fetchInvoices({
      status: statusFilter.value || undefined,
    })
  } catch (e) {
    console.error('Error loading invoices:', e)
  } finally {
    loading.value = false
  }
}

async function handleSend(id: string) {
  try {
    await sendInvoice(id)
    await loadInvoices()
  } catch (e) {
    console.error('Error sending invoice:', e)
  }
}

watch([statusFilter], loadInvoices)

onMounted(loadInvoices)
useHead({ title: 'Gestión de Facturas — Factura CR' })
</script>
