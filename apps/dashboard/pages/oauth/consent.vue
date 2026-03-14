<template>
  <div class="min-h-screen bg-zs-bg-primary flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-zs-bg-secondary border border-zs-border rounded-xl p-8 shadow-zs-glow-blue transition-all duration-300 hover:border-zs-primary/50">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zs-primary/10 mb-4 animate-pulse">
          <UIcon name="i-heroicons-shield-check" class="w-8 h-8 text-zs-primary" />
        </div>
        <h1 class="text-2xl font-bold text-zs-text-primary tracking-tight">
          Autorización de Acceso
        </h1>
        <p class="text-zs-text-secondary mt-2 text-sm italic">
          Zona Sur Tech Security Protocol
        </p>
      </div>

      <!-- App Info -->
      <div class="space-y-6">
        <div class="p-4 bg-zs-bg-primary/50 border border-zs-border rounded-lg">
          <p class="text-sm text-zs-text-primary leading-relaxed">
            La aplicación <span class="text-zs-primary font-mono uppercase tracking-widest text-xs">FacturaCR SaaS</span> solicita permiso para acceder a tu cuenta de Supabase.
          </p>
        </div>

        <div class="space-y-3">
          <p class="text-xs font-semibold text-zs-text-secondary uppercase tracking-widest px-1">
            Permisos solicitados:
          </p>
          <ul class="space-y-2">
            <li v-for="(scope, index) in scopes" :key="index" class="flex items-start gap-3 group">
              <UIcon name="i-heroicons-check-circle" class="w-5 h-5 text-zs-success mt-0.5 group-hover:scale-110 transition-transform" />
              <span class="text-sm text-zs-text-secondary group-hover:text-zs-text-primary transition-colors">{{ scope }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Actions -->
      <div class="mt-10 flex flex-col gap-3">
        <UButton
          block
          size="lg"
          color="primary"
          class="font-bold tracking-widest uppercase text-xs"
          @click="handleAuthorize"
        >
          Confirmar Acceso
        </UButton>
        <UButton
          block
          size="lg"
          variant="ghost"
          color="white"
          class="font-bold tracking-widest uppercase text-xs opacity-60 hover:opacity-100"
          @click="handleCancel"
        >
          Rechazar
        </UButton>
      </div>

      <!-- Footer -->
      <div class="mt-8 pt-6 border-t border-zs-border/30 text-center">
        <p class="text-[10px] text-zs-text-secondary/50 font-mono">
          SEC-AUTH // SESSIONID: {{ sessionId }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const scopes = [
  'Perfil de usuario y correo electrónico',
  'Gestión de facturación electrónica (Hacienda)',
  'Lectura/Escritura en módulos de ERP locales'
]

const sessionId = ref(Math.random().toString(36).substring(7).toUpperCase())

const handleAuthorize = () => {
  // TODO: Logic for OAuth authorization redirect
  console.log('User authorized')
}

const handleCancel = () => {
  // TODO: Redirect back or to error
  console.log('User cancelled')
}

definePageMeta({
  layout: false
})

useHead({
  title: 'Authorize Access | FacturaCR SaaS'
})
</script>

<style scoped>
.shadow-zs-glow-blue {
  box-shadow: 0 0 30px -10px rgba(59, 130, 246, 0.1);
}
</style>
