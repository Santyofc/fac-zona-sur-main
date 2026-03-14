<template>
  <NuxtLayout>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem;">
      <div>
        <h1 class="fcr-page-title">Suscripción y Pagos</h1>
        <p class="fcr-page-subtitle">Gestiona tu plan Creador y tu historial de facturación</p>
      </div>
      
      <!-- Current Plan Status Badge -->
      <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 99px; padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.5rem;">
        <span style="display: block; width: 8px; height: 8px; border-radius: 50%; background: #10B981;"></span>
        <span style="font-size: 0.875rem; font-weight: 600; color: #10B981;">Plan {{ currentPlan.name }} Activo</span>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; max-width: 1200px;">
      
      <!-- Left Column: Payment Methods & History -->
      <div style="display: flex; flex-direction: column; gap: 1.5rem;">
        
        <!-- Payment Options Card -->
        <div class="fcr-card">
          <h2 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--fcr-text-primary);">Renovar Suscripción</h2>
          <p style="font-size: 0.875rem; color: var(--fcr-text-muted); margin-bottom: 1.5rem;">
            Tu suscripción actual vence el <strong style="color: var(--fcr-text-primary)">{{ currentPlan.expiresAt }}</strong>.
            Puedes renovar por un mes adicional ({{ currentPlan.price }}) usando cualquiera de los siguientes métodos.
          </p>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            
            <!-- PayPal Option -->
            <div style="border: 1px solid var(--fcr-border); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; align-items: center; text-align: center; background: rgba(0,0,0,0.2);">
              <div style="font-size: 2rem; margin-bottom: 1rem;">💳</div>
              <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; color: #0070ba;">PayPal</h3>
              <p style="font-size: 0.75rem; color: var(--fcr-text-muted); margin-bottom: 1.5rem;">Activación inmediata. Acepta todas las tarjetas de crédito y débito internacionales.</p>
              
              <button 
                @click="startPaypalCheckout" 
                class="fcr-btn" 
                :disabled="isProcessingPaypal"
                style="width: 100%; background: #0070ba; color: white; border: none; font-weight: 600;"
              >
                {{ isProcessingPaypal ? 'Procesando...' : 'Pagar con PayPal' }}
              </button>
            </div>

            <!-- SINPE Option -->
            <div style="border: 1px solid var(--fcr-border); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; align-items: center; text-align: center; background: rgba(0,0,0,0.2);">
              <div style="font-size: 2rem; margin-bottom: 1rem;">📱</div>
              <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; color: #D1D5DB;">SINPE Móvil</h3>
              <p style="font-size: 0.75rem; color: var(--fcr-text-muted); margin-bottom: 1.5rem;">Activación manual (hasta 24h). Transfiere al <strong style="color:var(--fcr-text-secondary)">8888-8888</strong>.</p>
              
              <button 
                @click="showSinpeModal = true" 
                class="fcr-btn fcr-btn-outline" 
                style="width: 100%;"
              >
                Reportar Pago
              </button>
            </div>
          </div>
        </div>

        <!-- Payment History Table -->
        <div class="fcr-card">
          <h2 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 1.5rem; color: var(--fcr-text-primary);">Historial de Pagos</h2>
          
          <div v-if="loadingHistory" style="text-align: center; padding: 2rem; color: var(--fcr-text-muted);">
            Cargando historial...
          </div>
          
          <div v-else-if="payments.length === 0" style="text-align: center; padding: 2rem; color: var(--fcr-text-muted); font-size: 0.875rem;">
            Aún no tienes registros de pago.
          </div>
          
          <table v-else class="w-full text-left" style="font-size: 0.875rem;">
            <thead>
              <tr style="border-bottom: 1px solid var(--fcr-border); color: var(--fcr-text-muted);">
                <th class="pb-2 font-medium">Fecha</th>
                <th class="pb-2 font-medium">Método</th>
                <th class="pb-2 font-medium">Monto</th>
                <th class="pb-2 font-medium">Referencia</th>
                <th class="pb-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="payment in payments" :key="payment.id" style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td class="py-3 text-[var(--fcr-text-secondary)]">{{ formatDate(payment.created_at) }}</td>
                <td class="py-3">
                  <span v-if="payment.payment_method === 'paypal'" style="color: #0070ba; font-weight: 500;">PayPal</span>
                  <span v-else style="color: #D1D5DB; font-weight: 500;">SINPE</span>
                </td>
                <td class="py-3">{{ payment.currency }} {{ payment.amount }}</td>
                <td class="py-3 text-[var(--fcr-text-muted)] font-mono text-xs">{{ payment.reference_id || 'N/A' }}</td>
                <td class="py-3">
                  <span :class="getStatusBadgeClass(payment.status)">
                    {{ getStatusText(payment.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>

      <!-- Right Column: Plan Details -->
      <div style="display: flex; flex-direction: column; gap: 1.5rem;">
        
        <!-- Summary Card -->
        <div class="fcr-card" style="background: linear-gradient(180deg, rgba(37,99,235,0.05) 0%, rgba(0,0,0,0) 100%);">
          <h3 style="font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--fcr-text-muted); font-weight: 600; margin-bottom: 1rem;">Tu Plan</h3>
          
          <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 2.5rem; font-weight: 700; color: var(--fcr-text-primary);">{{ currentPlan.price }}</span>
            <span style="font-size: 0.875rem; color: var(--fcr-text-muted);">/ mes</span>
          </div>
          
          <p style="font-size: 0.875rem; color: var(--fcr-text-secondary); margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--fcr-border);">
            Plan {{ currentPlan.name }} ideal para profesionales independientes y pequeñas empresas.
          </p>
          
          <ul style="display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.875rem; color: var(--fcr-text-secondary);">
            <li style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="color: #10B981;">✓</span> Facturas Ilimitadas
            </li>
            <li style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="color: #10B981;">✓</span> Conexión ATV Hacienda
            </li>
            <li style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="color: #10B981;">✓</span> Firma Digital (XAdES)
            </li>
            <li style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="color: #10B981;">✓</span> Soporte por Email
            </li>
          </ul>
        </div>
        
        <!-- Support Card -->
        <div class="fcr-card">
          <h3 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--fcr-text-primary);">¿Necesitas ayuda?</h3>
          <p style="font-size: 0.75rem; color: var(--fcr-text-muted); margin-bottom: 1rem;">
            Si tuviste un problema con tu pago o necesitas cambiar tu plan, contáctanos.
          </p>
          <a href="mailto:soporte@zonasurtech.online" class="fcr-btn fcr-btn-outline" style="width: 100%; display: block; text-align: center; text-decoration: none; font-size: 0.875rem;">
            Contactar Soporte
          </a>
        </div>
      </div>
    </div>

    <!-- Modal SINPE -->
    <div v-if="showSinpeModal" style="position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 50;">
      <div class="fcr-card" style="width: 100%; max-width: 400px; padding: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
          <h3 style="font-size: 1.125rem; font-weight: 600;">Reportar Pago SINPE</h3>
          <button @click="showSinpeModal = false" style="background: none; border: none; color: var(--fcr-text-muted); cursor: pointer; font-size: 1.25rem;">&times;</button>
        </div>
        
        <p style="font-size: 0.875rem; color: var(--fcr-text-secondary); margin-bottom: 1.5rem;">
          Transfiere <strong style="color: var(--fcr-text-primary)">₡10,000</strong> (equivalente a $19.99) al número <strong style="color: var(--fcr-text-primary)">8888-8888</strong> (A nombre de Zona Sur Tech) e ingresa el número de comprobante abajo.
        </p>

        <form @submit.prevent="submitSinpeReport" style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <label class="fcr-label">Número de Comprobante *</label>
            <input v-model="sinpeForm.reference_id" type="text" class="fcr-input" required placeholder="Ej: 12345678" />
          </div>
          
          <div>
            <label class="fcr-label">Notas (Opcional)</label>
            <textarea v-model="sinpeForm.notes" class="fcr-input" rows="2" placeholder="Algún comentario adicional..."></textarea>
          </div>
          
          <div style="display: flex; gap: 1rem; margin-top: 1rem;">
            <button type="button" @click="showSinpeModal = false" class="fcr-btn fcr-btn-outline" style="flex: 1;">Cancelar</button>
            <button type="submit" class="fcr-btn fcr-btn-primary" style="flex: 1;" :disabled="isSubmittingSinpe">
              {{ isSubmittingSinpe ? 'Enviando...' : 'Enviar Reporte' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

useHead({ title: 'Suscripción y Pagos — Factura CR' })

// --- Mocks Data ---
const currentPlan = reactive({
  name: 'Pro',
  price: '$19.99',
  expiresAt: '25 Oct 2026'
})

const payments = ref<any[]>([])
const loadingHistory = ref(true)

// --- PayPal Logic ---
const isProcessingPaypal = ref(false)

async function startPaypalCheckout() {
  isProcessingPaypal.value = true
  
  try {
    // 1. Llamar a nuestro backend para crear la orden
    // const res = await $fetch('/api/payments/paypal/create', { method: 'POST', body: { plan_id: 'pro', months: 1 } })
    // const orderId = res.order_id
    
    // MOCK: Simular un delay
    await new Promise(r => setTimeout(r, 1000))
    alert("Redirigiendo a PayPal para completar el pago...\n(Flujo simulado completado con éxito)")
    
    // 2. Simular éxito tras volver de PayPal
    payments.value.unshift({
      id: Date.now().toString(),
      created_at: new Date().toISOString(),
      amount: "19.99",
      currency: "USD",
      payment_method: "paypal",
      reference_id: `PAYPAL-MOCK-${Date.now()}`,
      status: "approved"
    })
    
  } catch (err) {
    alert("Error procesando pago con PayPal")
  } finally {
    isProcessingPaypal.value = false
  }
}

// --- SINPE Logic ---
const showSinpeModal = ref(false)
const isSubmittingSinpe = ref(false)
const sinpeForm = reactive({
  reference_id: '',
  notes: ''
})

async function submitSinpeReport() {
  isSubmittingSinpe.value = true
  
  try {
    // const res = await $fetch('/api/payments/manual', {
    //   method: 'POST',
    //   body: {
    //     amount: 19.99,
    //     currency: 'CRC',
    //     payment_method: 'manual',
    //     reference_id: sinpeForm.reference_id,
    //     notes: sinpeForm.notes
    //   }
    // })
    
    await new Promise(r => setTimeout(r, 800))
    
    payments.value.unshift({
      id: Date.now().toString(),
      created_at: new Date().toISOString(),
      amount: "10000.00",
      currency: "CRC",
      payment_method: "manual",
      reference_id: sinpeForm.reference_id,
      status: "pending"
    })
    
    showSinpeModal.value = false
    sinpeForm.reference_id = ''
    sinpeForm.notes = ''
    alert("Reporte enviado con éxito. Un administrador lo revisará.")
    
  } catch (err) {
    alert("Error enviando reporte")
  } finally {
    isSubmittingSinpe.value = false
  }
}

// --- Lifecycle & Utils ---
onMounted(async () => {
  // Simular carga de historial
  await new Promise(r => setTimeout(r, 800))
  
  payments.value = [
    {
      id: '1',
      created_at: '2026-09-25T10:00:00Z',
      amount: "19.99",
      currency: "USD",
      payment_method: "paypal",
      reference_id: "PAY-123456",
      status: "approved"
    },
    {
       id: '2',
      created_at: '2026-08-25T14:30:00Z',
      amount: "10000.00",
      currency: "CRC",
      payment_method: "manual",
      reference_id: "SINPE-998877",
      status: "approved"
    }
  ]
  loadingHistory.value = false
})

function formatDate(isoString: string) {
  const d = new Date(isoString)
  return new Intl.DateTimeFormat('es-CR', { dateStyle: 'medium' }).format(d)
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: 'Pendiente',
    approved: 'Aprobado',
    rejected: 'Rechazado'
  }
  return map[status] || status
}

function getStatusBadgeClass(status: string) {
  const base = "px-2 py-1 text-xs font-medium rounded-full "
  if (status === 'approved') return base + 'bg-emerald-500/10 text-emerald-500'
  if (status === 'pending') return base + 'bg-amber-500/10 text-amber-500'
  if (status === 'rejected') return base + 'bg-red-500/10 text-red-500'
  return base + 'bg-gray-500/10 text-gray-500'
}
</script>
