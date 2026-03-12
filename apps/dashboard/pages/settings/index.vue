<template>
  <NuxtLayout>
    <h1 class="fcr-page-title">Configuración</h1>
    <p class="fcr-page-subtitle">Datos de la empresa y credenciales Hacienda</p>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 900px;">
      <!-- Datos de la empresa -->
      <div class="fcr-card">
        <h2 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">🏢 Datos de la Empresa</h2>
        <form @submit.prevent="saveCompany" style="display: flex; flex-direction: column; gap: 0.875rem;">
          <div>
            <label class="fcr-label">Razón Social *</label>
            <input v-model="company.name" class="fcr-input" required />
          </div>
          <div>
            <label class="fcr-label">Nombre Comercial</label>
            <input v-model="company.trade_name" class="fcr-input" />
          </div>
          <div class="fcr-grid-2">
            <div>
              <label class="fcr-label">Tipo Cédula</label>
              <select v-model="company.cedula_type" class="fcr-input" style="cursor: pointer;">
                <option value="FISICA">Cédula Física</option>
                <option value="JURIDICA">Cédula Jurídica</option>
              </select>
            </div>
            <div>
              <label class="fcr-label">Número de Cédula *</label>
              <input v-model="company.cedula_number" class="fcr-input" required placeholder="3-101-000000" />
            </div>
          </div>
          <div>
            <label class="fcr-label">Correo Electrónico *</label>
            <input v-model="company.email" type="email" class="fcr-input" required />
          </div>
          <div>
            <label class="fcr-label">Teléfono</label>
            <input v-model="company.phone" class="fcr-input" placeholder="+506 2222-2222" />
          </div>
          <div>
            <label class="fcr-label">Actividad Económica (CIIU)</label>
            <input v-model="company.actividad_economica" class="fcr-input" placeholder="722000" />
          </div>
          <div>
            <label class="fcr-label">Provincia</label>
            <select v-model="company.province" class="fcr-input" style="cursor: pointer;">
              <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          <div>
            <label class="fcr-label">Dirección</label>
            <textarea v-model="company.address" class="fcr-input" rows="2" style="resize: vertical;"></textarea>
          </div>
          <button type="submit" class="fcr-btn fcr-btn-primary" :disabled="saving">
            {{ saving ? 'Guardando...' : '💾 Guardar Empresa' }}
          </button>
        </form>
      </div>

      <!-- Credenciales Hacienda -->
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="fcr-card">
          <h2 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">🔐 Credenciales Hacienda CR</h2>
          <p style="font-size: 0.8rem; color: var(--fcr-text-muted); margin-bottom: 1rem;">
            Credenciales del ATV (Administración Tributaria Virtual). Requeridas para envío real de comprobantes.
          </p>
          <div style="display: flex; flex-direction: column; gap: 0.875rem;">
            <div>
              <label class="fcr-label">Ambiente</label>
              <select v-model="settings.hacienda_env" class="fcr-input" style="cursor: pointer;">
                <option value="sandbox">🧪 Sandbox (Pruebas)</option>
                <option value="production">🟢 Producción</option>
              </select>
            </div>
            <div>
              <label class="fcr-label">Usuario ATV (correo)</label>
              <input v-model="settings.hacienda_username" type="email" class="fcr-input" placeholder="usuario@atv.hacienda.go.cr" />
            </div>
            <div>
              <label class="fcr-label">Contraseña ATV</label>
              <input v-model="settings.hacienda_password" type="password" class="fcr-input" />
            </div>
            <div style="background: rgba(37,99,235,0.05); border: 1px solid rgba(37,99,235,0.15); border-radius: 8px; padding: 0.75rem;">
              <div style="font-size: 0.8rem; font-weight: 600; margin-bottom: 0.4rem; color: var(--fcr-blue-light);">📂 Certificado Digital .p12</div>
              <p style="font-size: 0.75rem; color: var(--fcr-text-muted);">
                Suba el certificado BCCR (.p12) para habilitarla firma digital XAdES. Emitido por el Banco Central de Costa Rica.
              </p>
              <div style="margin-top: 0.625rem; display: flex; align-items: center; gap: 0.5rem;">
                <span :style="{ color: certStatus.color, fontSize: '0.75rem' }">{{ certStatus.icon }} {{ certStatus.text }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="fcr-card">
          <h2 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">⚡ Estado del Sistema</h2>
          <div style="display: flex; flex-direction: column; gap: 0.625rem; font-size: 0.875rem;">
            <div v-for="status in systemStatus" :key="status.label"
              style="display: flex; justify-content: space-between; align-items: center;">
              <span style="color: var(--fcr-text-secondary);">{{ status.label }}</span>
              <span :style="{ color: status.ok ? '#10B981' : '#EF4444' }">
                {{ status.ok ? '✅ OK' : '❌ Error' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
const saving = ref(false)

const company = reactive({
  name: 'Empresa Tica SRL',
  trade_name: '',
  cedula_type: 'JURIDICA',
  cedula_number: '3-101-000000',
  email: 'empresa@example.cr',
  phone: '',
  province: 'San José',
  address: '',
  actividad_economica: '722000',
})

const settings = reactive({
  hacienda_env: 'sandbox',
  hacienda_username: '',
  hacienda_password: '',
})

const provinces = ['San José', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limón']

const certStatus = computed(() => ({
  icon: '⚠️',
  text: 'Sin certificado — Modo sandbox',
  color: '#F59E0B',
}))

const systemStatus = [
  { label: 'API Hacienda Sandbox', ok: true },
  { label: 'Base de datos',        ok: true },
  { label: 'Firma digital (.p12)', ok: false },
  { label: 'Generador PDF',        ok: true },
  { label: 'Cola de trabajos',     ok: true },
]

async function saveCompany() {
  saving.value = true
  await new Promise(r => setTimeout(r, 600)) // Simular save
  saving.value = false
}

useHead({ title: 'Configuración — Factura CR' })
</script>
