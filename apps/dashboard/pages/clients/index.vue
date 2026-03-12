<template>
  <NuxtLayout>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 class="fcr-page-title">Clientes</h1>
        <p class="fcr-page-subtitle">Directorio de receptores de facturas</p>
      </div>
      <button class="fcr-btn fcr-btn-primary" @click="showForm = true">➕ Nuevo Cliente</button>
    </div>

    <!-- Search -->
    <div class="fcr-card" style="margin-bottom: 1rem;">
      <input v-model="search" type="text" class="fcr-input" style="max-width: 320px;"
        placeholder="Buscar por nombre..." @input="debouncedLoad" />
    </div>

    <!-- Table -->
    <div class="fcr-card">
      <table class="fcr-table">
        <thead><tr>
          <th>Nombre</th><th>Cédula</th><th>Email</th><th>Teléfono</th><th>Acciones</th>
        </tr></thead>
        <tbody>
          <tr v-for="c in clients" :key="c.id">
            <td style="font-weight: 600; color: var(--fcr-text-primary);">{{ c.name }}</td>
            <td style="font-family: monospace; font-size: 0.8rem;">{{ c.cedula_number || '—' }}</td>
            <td>{{ c.email || '—' }}</td>
            <td>{{ c.phone || '—' }}</td>
            <td>
              <button class="fcr-btn fcr-btn-ghost" style="padding: 0.25rem 0.625rem; font-size: 0.75rem;"
                @click="editClient(c)">Editar</button>
            </td>
          </tr>
          <tr v-if="!clients.length">
            <td colspan="5" style="text-align: center; padding: 2rem; color: var(--fcr-text-muted);">
              No hay clientes registrados
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Form Modal (simplified) -->
    <ClientForm v-if="showForm" :client="editingClient"
      @save="handleSave" @cancel="closeForm" />
  </NuxtLayout>
</template>

<script setup lang="ts">
const { fetchClients, createClient, updateClient } = useClients()
const clients = ref([])
const search = ref('')
const showForm = ref(false)
const editingClient = ref(null)

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedLoad = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadClients, 400)
}

async function loadClients() {
  clients.value = await fetchClients({ search: search.value || undefined })
}

function editClient(c: unknown) {
  editingClient.value = c
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingClient.value = null
}

async function handleSave(data: Record<string, unknown>) {
  if (editingClient.value) {
    await updateClient(editingClient.value.id, data)
  } else {
    await createClient(data)
  }
  closeForm()
  await loadClients()
}

onMounted(loadClients)
useHead({ title: 'Clientes — Factura CR' })
</script>
