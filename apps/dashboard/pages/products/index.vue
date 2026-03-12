<template>
  <NuxtLayout>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 class="fcr-page-title">Productos y Servicios</h1>
        <p class="fcr-page-subtitle">Catálogo de ítems facturables con código CABYS</p>
      </div>
      <button class="fcr-btn fcr-btn-primary" @click="showForm = true">➕ Nuevo Producto</button>
    </div>

    <div class="fcr-card">
      <table class="fcr-table">
        <thead><tr>
          <th>Código</th><th>CABYS</th><th>Nombre</th><th>Precio Unit.</th><th>IVA</th><th>Acciones</th>
        </tr></thead>
        <tbody>
          <tr v-for="p in products" :key="p.id">
            <td style="font-family: monospace; font-size: 0.8rem;">{{ p.code || '—' }}</td>
            <td style="font-family: monospace; font-size: 0.8rem;">{{ p.cabys_code || '—' }}</td>
            <td style="font-weight: 600; color: var(--fcr-text-primary);">{{ p.name }}</td>
            <td style="font-weight: 600;">
              {{ formatCurrency(p.unit_price, p.currency) }}
            </td>
            <td>
              <span class="fcr-badge badge-accepted">{{ p.tax_rate }}%</span>
            </td>
            <td>
              <button class="fcr-btn fcr-btn-ghost" style="padding: 0.25rem 0.625rem; font-size: 0.75rem;"
                @click="editProduct(p)">Editar</button>
            </td>
          </tr>
          <tr v-if="!products.length">
            <td colspan="6" style="text-align: center; padding: 2rem; color: var(--fcr-text-muted);">
              No hay productos registrados
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
const { fetchProducts, updateProduct, createProduct } = useProducts()
const products = ref([])
const showForm = ref(false)
const editingProduct = ref(null)

const formatCurrency = (v: number, currency = 'CRC') =>
  new Intl.NumberFormat('es-CR', { style: 'currency', currency, minimumFractionDigits: 0 }).format(Number(v))

function editProduct(p: unknown) {
  editingProduct.value = p
  showForm.value = true
}

onMounted(async () => { products.value = await fetchProducts() })
useHead({ title: 'Productos — Factura CR' })
</script>
