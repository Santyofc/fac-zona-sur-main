<template>
  <!-- Full-screen modal overlay -->
  <div style="position: fixed; inset: 0; background: rgba(5, 12, 24, 0.85); backdrop-filter: blur(6px); z-index: 100; display: flex; align-items: center; justify-content: center; padding: 1rem;"
    @click.self="$emit('cancel')">
    <div class="fcr-card" style="width: 100%; max-width: 560px; max-height: 90vh; overflow-y: auto;">
      <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1.25rem;">
        {{ client ? 'Editar Cliente' : 'Nuevo Cliente' }}
      </h2>

      <form @submit.prevent="handleSubmit" style="display: flex; flex-direction: column; gap: 1rem;">
        <div>
          <label class="fcr-label">Nombre *</label>
          <input v-model="form.name" class="fcr-input" required placeholder="Empresa o Persona Física" />
        </div>

        <div class="fcr-grid-2">
          <div>
            <label class="fcr-label">Tipo de Identificación</label>
            <select v-model="form.cedula_type" class="fcr-input" style="cursor: pointer;">
              <option value="FISICA">Cédula Física</option>
              <option value="JURIDICA">Cédula Jurídica</option>
              <option value="DIMEX">DIMEX</option>
              <option value="NITE">NITE</option>
              <option value="EXTRANJERO">Extranjero</option>
            </select>
          </div>
          <div>
            <label class="fcr-label">Número de Cédula</label>
            <input v-model="form.cedula_number" class="fcr-input" placeholder="1-2345-6789" />
          </div>
        </div>

        <div class="fcr-grid-2">
          <div>
            <label class="fcr-label">Correo Electrónico</label>
            <input v-model="form.email" type="email" class="fcr-input" placeholder="cliente@empresa.cr" />
          </div>
          <div>
            <label class="fcr-label">Teléfono</label>
            <input v-model="form.phone" class="fcr-input" placeholder="+506 8888-8888" />
          </div>
        </div>

        <div>
          <label class="fcr-label">Provincia</label>
          <select v-model="form.province" class="fcr-input" style="cursor: pointer;">
            <option value="">— Seleccionar —</option>
            <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <div>
          <label class="fcr-label">Dirección</label>
          <textarea v-model="form.address" class="fcr-input" rows="2"
            placeholder="Dirección exacta del cliente" style="resize: vertical;"></textarea>
        </div>

        <div>
          <label class="fcr-label">Notas internas</label>
          <textarea v-model="form.notes" class="fcr-input" rows="2"
            placeholder="Notas de uso interno..." style="resize: vertical;"></textarea>
        </div>

        <div style="display: flex; gap: 0.75rem; justify-content: flex-end; padding-top: 0.5rem;">
          <button type="button" class="fcr-btn fcr-btn-ghost" @click="$emit('cancel')">Cancelar</button>
          <button type="submit" class="fcr-btn fcr-btn-primary" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar Cliente' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Client {
  id?: string
  name?: string
  cedula_type?: string
  cedula_number?: string
  email?: string
  phone?: string
  province?: string
  address?: string
  notes?: string
}

const props = defineProps<{ client?: Client | null }>()

const emit = defineEmits<{
  (e: 'save', data: Client): void
  (e: 'cancel'): void
}>()

const saving = ref(false)

const provinces = ['San José', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limón']

const form = reactive<Client>({
  name: props.client?.name || '',
  cedula_type: props.client?.cedula_type || 'FISICA',
  cedula_number: props.client?.cedula_number || '',
  email: props.client?.email || '',
  phone: props.client?.phone || '',
  province: props.client?.province || '',
  address: props.client?.address || '',
  notes: props.client?.notes || '',
})

async function handleSubmit() {
  saving.value = true
  try {
    emit('save', { ...form })
  } finally {
    saving.value = false
  }
}
</script>
