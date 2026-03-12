<template>
  <div class="fcr-layout">
    <!-- Sidebar -->
    <aside class="fcr-sidebar">
      <!-- Logo -->
      <div class="fcr-sidebar-logo">
        <div class="fcr-logo-icon">
          <span style="color: white">₡</span>
        </div>
        <span class="fcr-logo-text">Factura CR</span>
      </div>

      <!-- Navigation -->
      <nav class="fcr-nav">
        <div class="fcr-nav-label">Principal</div>
        <NuxtLink v-for="item in navItems" :key="item.to" :to="item.to"
          class="fcr-nav-item" :class="{ active: isActive(item.to) }">
          <component :is="item.icon" class="fcr-nav-icon" />
          {{ item.label }}
        </NuxtLink>

        <div class="fcr-nav-label" style="margin-top: 1rem">Configuración</div>
        <NuxtLink to="/settings" class="fcr-nav-item" :class="{ active: isActive('/settings') }">
          <CogIcon class="fcr-nav-icon" />
          Configuración
        </NuxtLink>
      </nav>

      <!-- User Info -->
      <div style="padding: 1rem; border-top: 1px solid var(--fcr-border);">
        <div style="display: flex; align-items: center; gap: 0.625rem;">
          <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #06B6D4); display: flex; align-items: center; justify-content: center; font-size: 0.875rem; font-weight: 700; color: white;">
            {{ userInitial }}
          </div>
          <div>
            <div style="font-size: 0.8rem; font-weight: 600; color: var(--fcr-text-primary);">{{ userName }}</div>
            <div style="font-size: 0.7rem; color: var(--fcr-text-muted);">{{ companyName }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main -->
    <main class="fcr-main">
      <!-- Topbar -->
      <header class="fcr-topbar">
        <div style="font-size: 0.875rem; color: var(--fcr-text-secondary);">
          {{ currentPageTitle }}
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <NuxtLink to="/invoices/new">
            <button class="fcr-btn fcr-btn-primary">
              <PlusIcon style="width: 16px; height: 16px;" />
              Nueva Factura
            </button>
          </NuxtLink>
        </div>
      </header>

      <!-- Page Content -->
      <div class="fcr-page fcr-animate-in">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

// ─── Nav items ──────────────────────────────────────────────
const navItems = [
  { to: '/',          label: 'Dashboard',  icon: 'HomeIcon' },
  { to: '/invoices',  label: 'Facturas',   icon: 'DocumentTextIcon' },
  { to: '/clients',   label: 'Clientes',   icon: 'UsersIcon' },
  { to: '/products',  label: 'Productos',  icon: 'CubeIcon' },
  { to: '/reports',   label: 'Reportes',   icon: 'ChartBarIcon' },
]

const pageTitles: Record<string, string> = {
  '/':           'Dashboard',
  '/invoices':   'Facturas',
  '/clients':    'Clientes',
  '/products':   'Productos',
  '/reports':    'Reportes',
  '/settings':   'Configuración',
}

const currentPageTitle = computed(() =>
  pageTitles[route.path] || pageTitles[`/${route.path.split('/')[1]}`] || 'Factura CR'
)

const isActive = (to: string) => {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

// ─── User/Company from localStorage/composable ───────────────
const userName = ref('Usuario')
const companyName = ref('Mi Empresa')
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

// Heroicons inline SVG components (minimal)
const HomeIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>`
})
const DocumentTextIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>`
})
const UsersIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" /></svg>`
})
const CubeIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>`
})
const ChartBarIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>`
})
const CogIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>`
})
const PlusIcon = defineComponent({
  template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>`
})
</script>
