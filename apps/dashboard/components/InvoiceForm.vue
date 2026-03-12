<template>
  <div style="position: fixed; inset: 0; background: rgba(5, 12, 24, 0.9); backdrop-filter: blur(8px); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 1rem;"
    @click.self="$emit('cancel')">
    <div class="fcr-card" style="width: 100%; max-width: 860px; max-height: 92vh; overflow-y: auto;">
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h2 style="font-size: 1.1rem; font-weight: 700;">Nueva Factura Electrónica</h2>
        <button class="fcr-btn fcr-btn-ghost" style="padding: 0.25rem;" @click="$emit('cancel')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <!-- Sección: Receptor -->
        <div style="margin-bottom: 1.25rem;">
          <div class="fcr-nav-label" style="margin-bottom: 0.75rem;">RECEPTOR</div>
          <div class="fcr-grid-2">
            <div>
              <label class="fcr-label">Cliente</label>
              <select v-model="form.client_id" class="fcr-input" style="cursor: pointer;">
                <option value="">— Consumidor Final —</option>
                <option v-for="c in clients" :key="c.id" :value="c.id">
                  {{ c.name }} — {{ c.cedula_number || 'Sin cédula' }}
                </option>
              </select>
            </div>
            <div class="fcr-grid-2">
              <div>
                <label class="fcr-label">Tipo Comprobante</label>
                <select v-model="form.doc_type" class="fcr-input" style="cursor: pointer;">
                  <option value="FE">Factura Electrónica</option>
                  <option value="TE">Tiquete Electrónico</option>
                  <option value="NC">Nota de Crédito</option>
                  <option value="ND">Nota de Débito</option>
                </select>
              </div>
              <div>
                <label class="fcr-label">Moneda</label>
                <select v-model="form.currency" class="fcr-input" style="cursor: pointer;">
                  <option value="CRC">₡ Colones (CRC)</option>
                  <option value="USD">$ Dólares (USD)</option>
                </select>
              </div>
            </div>
          </div>
          <div class="fcr-grid-2" style="margin-top: 0.75rem;">
            <div>
              <label class="fcr-label">Condición de Venta</label>
              <select v-model="form.sale_condition" class="fcr-input" style="cursor: pointer;">
                <option value="01">Contado</option>
                <option value="02">Crédito</option>
                <option value="03">Consignación</option>
                <option value="04">Apartado</option>
                <option value="05">Arrendamiento con opción</option>
                <option value="06">Arrendamiento en función financiera</option>
              </select>
            </div>
            <div>
              <label class="fcr-label">Medio de Pago</label>
              <select v-model="form.payment_method" class="fcr-input" style="cursor: pointer;">
                <option value="01">Efectivo</option>
                <option value="02">Tarjeta</option>
                <option value="03">Cheque</option>
                <option value="04">Transferencia</option>
                <option value="05">Recaudado por terceros</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Sección: Líneas de detalle -->
        <div style="margin-bottom: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <div class="fcr-nav-label">LÍNEAS DE DETALLE</div>
            <button type="button" class="fcr-btn fcr-btn-ghost" style="padding: 0.25rem 0.625rem; font-size: 0.75rem;"
              @click="addLine">+ Agregar Línea</button>
          </div>

          <div class="fcr-table-wrapper">
            <table class="fcr-table">
              <thead><tr>
                <th style="width: 140px;">Producto</th>
                <th>CABYS</th>
                <th>Descripción</th>
                <th style="width: 75px;">Cant.</th>
                <th style="width: 110px;">Precio U.</th>
                <th style="width: 75px;">Desc. %</th>
                <th style="width: 75px;">IVA %</th>
                <th style="width: 100px;">Total</th>
                <th style="width: 40px;"></th>
              </tr></thead>
              <tbody>
                <tr v-for="(line, idx) in form.items" :key="idx">
                  <!-- Producto -->
                  <td>
                    <select class="fcr-input" style="font-size: 0.75rem; padding: 0.3rem;"
                      @change="onProductSelected(idx, $event)">
                      <option value="">Manual</option>
                      <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                    </select>
                  </td>
                  <!-- CABYS -->
                  <td>
                    <input v-model="line.cabys_code" class="fcr-input"
                           style="font-size: 0.75rem; padding: 0.3rem; font-family: monospace; width: 110px;"
                           maxlength="13" placeholder="CABYS (13d)" />
                  </td>
                  <!-- Descripción -->
                  <td>
                    <input v-model="line.description" class="fcr-input"
                           style="font-size: 0.75rem; padding: 0.3rem; min-width: 120px;" required />
                  </td>
                  <!-- Cantidad -->
                  <td>
                    <input v-model.number="line.quantity" type="number" min="0.001" step="0.001"
                           class="fcr-input" style="font-size: 0.75rem; padding: 0.3rem;"
                           @input="recalcLine(idx)" />
                  </td>
                  <!-- Precio unitario -->
                  <td>
                    <input v-model.number="line.unit_price" type="number" min="0" step="0.01"
                           class="fcr-input" style="font-size: 0.75rem; padding: 0.3rem;"
                           @input="recalcLine(idx)" />
                  </td>
                  <!-- Descuento % -->
                  <td>
                    <input v-model.number="line.discount_pct" type="number" min="0" max="100" step="0.01"
                           class="fcr-input" style="font-size: 0.75rem; padding: 0.3rem;"
                           @input="recalcLine(idx)" />
                  </td>
                  <!-- IVA % -->
                  <td>
                    <select v-model.number="line.tax_rate" class="fcr-input"
                            style="font-size: 0.75rem; padding: 0.3rem; cursor: pointer;"
                            @change="recalcLine(idx)">
                      <option :value="13">13%</option>
                      <option :value="8">8%</option>
                      <option :value="4">4%</option>
                      <option :value="2">2%</option>
                      <option :value="1">1%</option>
                      <option :value="0">0% (Exento)</option>
                    </select>
                  </td>
                  <!-- Total línea -->
                  <td style="font-weight: 600; text-align: right; font-size: 0.8rem; color: var(--fcr-text-primary);">
                    {{ formatCRC(line.total) }}
                  </td>
                  <!-- Eliminar -->
                  <td>
                    <button type="button" style="background: none; border: none; color: #EF4444; cursor: pointer; font-size: 1rem;" @click="removeLine(idx)">✕</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Totales -->
        <div style="display: flex; justify-content: flex-end; margin-bottom: 1.25rem;">
          <div class="fcr-card" style="min-width: 320px; background: var(--fcr-bg-secondary);">
            <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.875rem;">
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--fcr-text-muted);">Subtotal:</span>
                <span>{{ formatCRC(totals.subtotal) }}</span>
              </div>
              <div v-if="totals.discount > 0" style="display: flex; justify-content: space-between; color: #EF4444;">
                <span>Descuentos:</span>
                <span>-{{ formatCRC(totals.discount) }}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--fcr-text-muted);">IVA Total:</span>
                <span>{{ formatCRC(totals.tax) }}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 1rem; font-weight: 700; padding-top: 0.5rem; border-top: 1px solid var(--fcr-border); margin-top: 0.25rem;">
                <span>TOTAL:</span>
                <span style="color: var(--fcr-blue-light);">{{ formatCRC(totals.total) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notas -->
        <div style="margin-bottom: 1.25rem;">
          <label class="fcr-label">Notas (opcional)</label>
          <textarea v-model="form.notes" class="fcr-input" rows="2"
            placeholder="Información adicional para el receptor..." style="resize: vertical;"></textarea>
        </div>

        <!-- Acciones -->
        <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
          <button type="button" class="fcr-btn fcr-btn-ghost" @click="$emit('cancel')">Cancelar</button>
          <button type="submit" class="fcr-btn fcr-btn-primary" :disabled="saving || !form.items.length">
            {{ saving ? 'Creando factura...' : '📄 Crear Factura' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const { createInvoice } = useInvoices()
const { fetchClients }  = useClients()
const { fetchProducts } = useProducts()

const emit = defineEmits<{
  (e: 'created', id: string): void
  (e: 'cancel'): void
}>()

const saving   = ref(false)
const clients  = ref([])
const products = ref([])

const form = reactive({
  client_id:       '',
  doc_type:        'FE',
  currency:        'CRC',
  sale_condition:  '01',
  payment_method:  '01',
  notes:           '',
  items:           [] as any[],
})

// Totales reactivos
const totals = computed(() => {
  let subtotal = 0, discount = 0, tax = 0, total = 0
  for (const line of form.items) {
    const base = (line.quantity || 0) * (line.unit_price || 0)
    const disc = base * ((line.discount_pct || 0) / 100)
    const net  = base - disc
    const taxA = net * ((line.tax_rate || 0) / 100)
    subtotal += base
    discount += disc
    tax      += taxA
    total    += net + taxA
  }
  return { subtotal, discount, tax, total }
})

function addLine() {
  form.items.push({
    product_id:   null,
    cabys_code:   '',
    description:  '',
    quantity:     1,
    unit_measure: 'Unid',
    unit_price:   0,
    discount_pct: 0,
    tax_rate:     13,
    total:        0,
  })
}

function removeLine(idx: number) {
  form.items.splice(idx, 1)
}

function recalcLine(idx: number) {
  const line = form.items[idx]
  const base = (line.quantity || 0) * (line.unit_price || 0)
  const disc = base * ((line.discount_pct || 0) / 100)
  const net  = base - disc
  const tax  = net * ((line.tax_rate || 0) / 100)
  line.total = net + tax
}

function onProductSelected(idx: number, event: Event) {
  const pid = (event.target as HTMLSelectElement).value
  const prod = products.value.find((p: any) => p.id === pid)
  if (!prod) return
  const line = form.items[idx]
  line.product_id   = pid
  line.cabys_code   = prod.cabys_code || ''
  line.description  = prod.name
  line.unit_price   = parseFloat(prod.unit_price)
  line.tax_rate     = parseFloat(prod.tax_rate || 13)
  line.unit_measure = prod.unit_measure || 'Unid'
  recalcLine(idx)
}

const formatCRC = (v: number) => {
  const sym = form.currency === 'CRC' ? '₡' : '$'
  const decimals = form.currency === 'CRC' ? 0 : 2
  return `${sym}${v.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
}

async function handleSubmit() {
  if (!form.items.length) return
  saving.value = true
  try {
    const payload = {
      client_id:      form.client_id || null,
      doc_type:       form.doc_type,
      currency:       form.currency,
      sale_condition: form.sale_condition,
      payment_method: form.payment_method,
      notes:          form.notes,
      items: form.items.map((item, i) => ({
        product_id:    item.product_id || null,
        cabys_code:    item.cabys_code || null,
        description:   item.description,
        quantity:      item.quantity,
        unit_measure:  item.unit_measure,
        unit_price:    item.unit_price,
        discount_pct:  item.discount_pct,
        tax_rate:      item.tax_rate,
      })),
    }
    const result = await createInvoice(payload) as any
    emit('created', result.id)
  } catch (e: any) {
    console.error('Error al crear factura:', e)
    alert(e?.message || 'Error al crear la factura')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  [clients.value, products.value] = await Promise.all([fetchClients(), fetchProducts()])
  addLine() // Agrega una línea inicial
})
</script>
