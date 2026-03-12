<template>
  <div style="min-height: 100vh; background: var(--fcr-bg-primary); display: flex; align-items: center; justify-content: center; padding: 1rem;">
    <!-- Background grid pattern -->
    <div style="position: fixed; inset: 0; background-image: linear-gradient(rgba(37, 99, 235, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 99, 235, 0.03) 1px, transparent 1px); background-size: 32px 32px; pointer-events: none;"></div>

    <div style="position: relative; width: 100%; max-width: 420px;">
      <!-- Logo -->
      <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display: inline-flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
          <div class="fcr-logo-icon" style="width: 48px; height: 48px; font-size: 1.4rem;">₡</div>
          <span style="font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #F1F5F9, #2563EB); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Factura CR</span>
        </div>
        <p style="color: var(--fcr-text-muted); font-size: 0.875rem;">Plataforma de comprobantes electrónicos</p>
      </div>

      <!-- Card -->
      <div class="fcr-card fcr-glow">
        <h1 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem;">Iniciar Sesión</h1>
        <p style="color: var(--fcr-text-muted); font-size: 0.875rem; margin-bottom: 1.5rem;">Accede a tu panel de facturación</p>

        <form @submit.prevent="handleLogin" style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <label class="fcr-label">Correo electrónico</label>
            <input v-model="email" type="email" class="fcr-input" required
              placeholder="empresa@example.cr" autocomplete="email" />
          </div>

          <div>
            <label class="fcr-label" style="display: flex; justify-content: space-between;">
              <span>Contraseña</span>
              <a href="#" style="font-size: 0.75rem; color: var(--fcr-blue-light);">¿Olvidaste tu contraseña?</a>
            </label>
            <div style="position: relative;">
              <input v-model="password" :type="showPass ? 'text' : 'password'" class="fcr-input" required
                placeholder="••••••••" autocomplete="current-password" style="padding-right: 44px;" />
              <button type="button"
                style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; color: var(--fcr-text-muted); font-size: 1rem;"
                @click="showPass = !showPass">{{ showPass ? '🙈' : '👁' }}</button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="error" style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 0.75rem; font-size: 0.875rem; color: #FCA5A5;">
            ❌ {{ error }}
          </div>

          <button type="submit" class="fcr-btn fcr-btn-primary" :disabled="loading"
            style="width: 100%; padding: 0.75rem; font-size: 0.9rem; margin-top: 0.25rem;">
            {{ loading ? 'Iniciando sesión...' : '→ Ingresar' }}
          </button>
        </form>

        <div style="text-align: center; margin-top: 1.25rem; font-size: 0.875rem; color: var(--fcr-text-muted);">
          ¿No tienes cuenta?
          <NuxtLink to="/auth/register" style="color: var(--fcr-blue-light); margin-left: 4px;">Crear empresa →</NuxtLink>
        </div>
      </div>

      <!-- Demo hint -->
      <div style="text-align: center; margin-top: 1rem; font-size: 0.75rem; color: var(--fcr-text-muted); opacity: 0.7;">
        Zona Sur Tech © 2026 · Comprobantes Electrónicos Hacienda CR
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { login } = useApi()
const router    = useRouter()

const email    = ref('')
const password = ref('')
const loading  = ref(false)
const showPass = ref(false)
const error    = ref('')

async function handleLogin() {
  loading.value = true
  error.value   = ''
  try {
    await login(email.value, password.value)
    await router.push('/')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Credenciales incorrectas. Intenta de nuevo.'
  } finally {
    loading.value = false
  }
}

definePageMeta({ layout: false })
useHead({ title: 'Iniciar Sesión — Factura CR' })
</script>
