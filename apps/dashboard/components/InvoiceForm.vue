<template>
  <div class="fixed inset-0 bg-zs-bg-primary/95 backdrop-blur-xl z-[200] flex items-center justify-center p-4"
    @click.self="$emit('cancel')">
    <div class="zs-card w-full max-w-[960px] max-h-[92vh] overflow-y-auto p-0 border-zs-blue/20 animate-scale-in">
      <!-- Header -->
      <div class="p-8 border-b border-white/5 flex items-center justify-between bg-zs-bg-secondary/40 backdrop-blur-md">
        <div>
          <h2 class="text-2xl font-black zs-text-gradient tracking-tight uppercase italic">Emitir Activo Digital</h2>
          <div class="flex items-center gap-2 mt-1">
            <div class="w-2 h-2 rounded-full bg-zs-blue animate-pulse"></div>
            <p class="text-[9px] text-zs-text-muted uppercase font-black tracking-[0.3em]">Hacienda Protocol v4.4 Secure Connection</p>
          </div>
        </div>
        <button class="p-2 rounded-xl hover:bg-white/5 text-zs-text-muted hover:text-white transition-all" @click="$emit('cancel')">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 space-y-8">
        <!-- Sección: Datos del Receptor -->
        <div class="space-y-6 animate-cascade animate-delay-100">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-1.5 h-4 bg-zs-blue rounded-full shadow-zs-glow-blue"></div>
            <h3 class="zs-heading-premium text-[11px]">Receptor del Activo</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest ml-1">Receptor</label>
              <select v-model="form.client_id" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white focus:border-zs-blue/40 outline-none transition-all cursor-pointer appearance-none">
                <option value="">— CONSUMIDOR FINAL —</option>
                <option v-for="c in clients" :key="c.id" :value="c.id">
                  {{ c.name.toUpperCase() }} — {{ c.cedula_number || 'SIN CÉDULA' }}
                </option>
              </select>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest ml-1">Tipo Documento</label>
                <select v-model="form.doc_type" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black text-white focus:border-zs-blue/40 outline-none transition-all cursor-pointer uppercase">
                  <option value="FE">Factura Electrónica</option>
                  <option value="TE">Tiquete Electrónico</option>
                  <option value="NC">Nota de Crédito</option>
                  <option value="ND">Nota de Débito</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest ml-1">Moneda</label>
                <select v-model="form.currency" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black text-white focus:border-zs-blue/40 outline-none transition-all cursor-pointer uppercase">
                  <option value="CRC">₡ COLONES (CRC)</option>
                  <option value="USD">$ DÓLARES (USD)</option>
                </select>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest ml-1">Condición de Venta</label>
              <select v-model="form.sale_condition" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black text-white focus:border-zs-blue/40 outline-none transition-all cursor-pointer uppercase">
                <option value="01">Contado</option>
                <option value="02">Crédito</option>
                <option value="03">Consignación</option>
                <option value="04">Apartado</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest ml-1">Medio de Pago</label>
              <select v-model="form.payment_method" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black text-white focus:border-zs-blue/40 outline-none transition-all cursor-pointer uppercase">
                <option value="01">Efectivo</option>
                <option value="02">Tarjeta</option>
                <option value="04">Transferencia</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Sección: Líneas de Detalle -->
        <div class="animate-cascade animate-delay-200">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-4 bg-zs-blue rounded-full shadow-zs-glow-blue"></div>
              <h3 class="zs-heading-premium text-[11px]">Matriz de Servicios</h3>
            </div>
            <button type="button" @click="addLine" class="zs-btn secondary py-2 px-4 !text-[9px]">
              + INSERTAR LÍNEA
            </button>
          </div>

          <div class="overflow-hidden rounded-2xl border border-white/5 bg-zs-bg-secondary/30 backdrop-blur-sm">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-white/[0.03] text-[9px] font-black uppercase tracking-[0.2em] text-zs-text-muted border-b border-white/5">
                  <th class="px-6 py-4 w-40">ITEM CODE</th>
                  <th class="px-6 py-4 w-32">CABYS ID</th>
                  <th class="px-6 py-4">DESCRIPCIÓN OPERATIVA</th>
                  <th class="px-6 py-4 w-20 text-center">CANT</th>
                  <th class="px-6 py-4 w-32 text-right">PRECIO U.</th>
                  <th class="px-6 py-4 w-24 text-center">TAX %</th>
                  <th class="px-6 py-4 w-36 text-right">TOTAL NETO</th>
                  <th class="px-6 py-4 w-12"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5">
                <tr v-for="(line, idx) in form.items" :key="idx" class="hover:bg-white/[0.02] transition-colors group">
                  <td class="px-4 py-4">
                    <select class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-black text-zs-text-secondary focus:border-zs-blue/40 transition-all cursor-pointer appearance-none px-3 py-2 uppercase" @change="onProductSelected(idx, $event)">
                      <option value="">MANUAL ENTRY</option>
                      <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                    </select>
                  </td>
                  <td class="px-4 py-4">
                    <input v-model="line.cabys_code" class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-mono font-bold text-zs-blue-lt focus:border-zs-blue/40 transition-all px-3 py-2 tracking-widest" maxlength="13" placeholder="0000..." />
                  </td>
                  <td class="px-4 py-4">
                    <input v-model="line.description" class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-bold text-white focus:border-zs-blue/40 transition-all px-3 py-2" placeholder="Describir..." required />
                  </td>
                  <td class="px-4 py-4">
                    <input v-model.number="line.quantity" type="number" step="0.001" class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-black text-white text-center focus:border-zs-blue/40 transition-all px-3 py-2" @input="recalcLine(idx)" />
                  </td>
                  <td class="px-4 py-4">
                    <input v-model.number="line.unit_price" type="number" step="0.01" class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-black text-white text-right focus:border-zs-blue/40 transition-all px-3 py-2" @input="recalcLine(idx)" />
                  </td>
                  <td class="px-4 py-4">
                    <select v-model.number="line.tax_rate" class="w-full bg-white/5 border border-white/5 rounded-lg text-[10px] font-black text-zs-text-secondary focus:border-zs-blue/40 transition-all cursor-pointer appearance-none px-3 py-2 text-center" @change="recalcLine(idx)">
                      <option :value="13">13%</option>
                      <option :value="8">8%</option>
                      <option :value="4">4%</option>
                      <option :value="2">2%</option>
                      <option :value="1">1%</option>
                      <option :value="0">0%</option>
                    </select>
                  </td>
                  <td class="px-6 py-4 text-right text-[11px] font-black text-white tracking-tight">
                    <span class="text-[9px] opacity-40 mr-1">$</span>{{ formatCurrencyAmountInTable(line.total) }}
                  </td>
                  <td class="px-2 py-4 text-center">
                    <button type="button" @click="removeLine(idx)" class="w-8 h-8 rounded-lg bg-zs-rose/10 text-zs-rose hover:bg-zs-rose hover:text-white transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                      ✕
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Totales & Resumen -->
        <div class="flex flex-col md:flex-row justify-between items-start gap-8 animate-cascade animate-delay-300">
          <div class="flex-1 w-full">
            <label class="text-[10px] font-black text-zs-text-muted uppercase tracking-widest mb-2 block ml-1">Notas Adicionales</label>
            <textarea v-model="form.notes" rows="3" class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white focus:border-zs-blue/40 outline-none transition-all resize-none placeholder:text-white/10" placeholder="Detalles de pago, órdenes de compra u otros datos..."></textarea>
          </div>

          <div class="w-full md:w-80 space-y-3 bg-white/[0.01] border border-white/5 rounded-2xl p-5">
            <div class="flex justify-between text-[10px] font-bold text-zs-text-muted uppercase">
              <span>Subtotal</span>
              <span class="text-white">{{ formatCRC(totals.subtotal) }}</span>
            </div>
            <div v-if="totals.discount > 0" class="flex justify-between text-[10px] font-bold text-zs-rose uppercase">
              <span>Descuentos</span>
              <span>-{{ formatCRC(totals.discount) }}</span>
            </div>
            <div class="flex justify-between text-[10px] font-bold text-zs-text-muted uppercase">
              <span>IVA Acumulado</span>
              <span class="text-white">{{ formatCRC(totals.tax) }}</span>
            </div>
            <div class="pt-3 border-t border-white/5 flex justify-between items-center">
              <span class="text-xs font-black text-white uppercase tracking-widest">Total Bruto</span>
              <span class="text-xl font-black text-zs-blue-lt tracking-tighter">{{ formatCRC(totals.total) }}</span>
            </div>
          </div>
        </div>

        <!-- Acciones Finales -->
        <div class="flex items-center justify-end gap-4 pt-6 mt-8 border-t border-white/5">
          <button type="button" @click="$emit('cancel')" class="px-6 py-3 rounded-xl hover:bg-white/5 text-[10px] font-black text-zs-text-muted uppercase tracking-widest transition-all">
            Descartar
          </button>
          <button type="submit" :disabled="saving || !form.items.length" class="zs-btn-primary px-8 py-3 flex items-center gap-2">
            <span v-if="saving" class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span class="text-[11px] font-black tracking-[0.2em] uppercase">
              {{ saving ? 'PROCESANDO...' : 'EMITIR COMPROBANTE' }}
            </span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'

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
  const prod = (products.value as any[]).find((p: any) => p.id === pid)
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

const formatCurrencyAmountInTable = (v: number) =>
  new Intl.NumberFormat('es-CR', {
    minimumFractionDigits: 0
  }).format(v || 0)

const formatCRC = (v: number) => {
  const num = v || 0
  return new Intl.NumberFormat('es-CR', {
    style: 'currency',
    currency: form.currency,
    minimumFractionDigits: form.currency === 'CRC' ? 0 : 2
  }).format(num)
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
      items: form.items.map((item) => ({
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
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [c, p] = await Promise.all([fetchClients(), fetchProducts()])
    clients.value = c as any
    products.value = p as any
    if (form.items.length === 0) addLine()
  } catch (e) {
    console.error('Error in InvoiceForm onMounted:', e)
  }
})
</script>
