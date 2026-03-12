<template>
  <div>
    <NuxtLayout>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h1 class="fcr-page-title">Facturas</h1>
          <p class="fcr-page-subtitle">Gestiona y envía tus comprobantes electrónicos</p>
        </div>
        <NuxtLink to="/invoices/new">
          <button class="fcr-btn fcr-btn-primary">➕ Nueva Factura</button>
        </NuxtLink>
      </div>

      <!-- Filters -->
      <div class="fcr-card" style="margin-bottom: 1rem; display: flex; gap: 0.75rem; align-items: center;">
        <input v-model="search" type="text" class="fcr-input" style="max-width: 280px;"
          placeholder="Buscar facturas..." />
        <select v-model="statusFilter" class="fcr-input" style="max-width: 160px; cursor: pointer;">
          <option value="">Todos los estados</option>
          <option value="draft">Borrador</option>
          <option value="processing">Procesando</option>
          <option value="sent">Enviada</option>
          <option value="accepted">Aceptada</option>
          <option value="rejected">Rechazada</option>
        </select>
        <button class="fcr-btn fcr-btn-ghost" @click="loadInvoices">🔄 Actualizar</button>
      </div>

      <!-- Table -->
      <div class="fcr-card">
        <InvoiceTable :invoices="invoices" :loading="loading" @send="handleSend" />
      </div>
    </NuxtLayout>
  </div>
</template>

<script setup lang="ts">
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
  } finally {
    loading.value = false
  }
}

async function handleSend(id: string) {
  await sendInvoice(id)
  await loadInvoices()
}

watch([statusFilter], loadInvoices)

onMounted(loadInvoices)
useHead({ title: 'Facturas — Factura CR' })
</script>
