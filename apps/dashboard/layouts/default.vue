<template>
  <div class="min-h-screen bg-zs-bg-primary text-zs-text-primary selection:bg-zs-blue/30 overflow-x-hidden">
    <!-- Decorative Orbs -->
    <div class="zs-orb w-[800px] h-[800px] bg-zs-blue/5 -top-60 -left-60 animate-pulse duration-[12s]"></div>
    <div class="zs-orb w-[500px] h-[500px] bg-zs-violet/5 bottom-0 -right-40 animate-pulse duration-[10s]"></div>

    <!-- Sidebar Wrapper -->
    <div class="flex relative">
      <!-- Sidebar -->
      <aside class="w-[280px] h-screen sticky top-0 bg-zs-bg-primary/95 backdrop-blur-3xl border-r border-white/5 hidden lg:flex flex-col z-[100] shadow-[10px_0_30px_rgba(0,0,0,0.5)]">
        <!-- Logo Section -->
        <div class="p-8 border-b border-white/5 group">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-zs-gradient-blue shadow-zs-glow-blue flex items-center justify-center relative overflow-hidden group-hover:scale-110 transition-transform duration-normal">
              <span class="text-white font-black text-lg relative z-10">₡</span>
              <div class="absolute inset-0 bg-white/20 animate-pulse"></div>
            </div>
            <div>
              <div class="font-black text-lg tracking-tight zs-text-gradient leading-none">FACTURA CR</div>
              <div class="text-[10px] uppercase tracking-[0.2em] text-zs-text-muted mt-1">SaaS Architecture</div>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 px-4 py-8 space-y-1 overflow-y-auto no-scrollbar">
          <div class="px-4 mb-4">
            <span class="text-[10px] font-black uppercase tracking-[0.2em] text-zs-text-muted">General</span>
          </div>
          
          <NuxtLink v-for="item in navItems" :key="item.to" :to="item.to"
            class="group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-fast relative"
            :class="isActive(item.to) ? 'bg-zs-blue/10 text-zs-blue-lt border border-zs-blue/20' : 'text-zs-text-secondary hover:bg-white/5 hover:text-zs-text-primary'">
            <component :is="item.icon" class="w-5 h-5 transition-transform duration-normal group-hover:scale-110" />
            <span class="text-sm font-semibold">{{ item.label }}</span>
            <div v-if="isActive(item.to)" class="absolute left-0 w-1 h-6 bg-zs-blue rounded-r-full shadow-zs-glow-blue"></div>
          </NuxtLink>

          <div class="px-4 mt-8 mb-4">
            <span class="text-[10px] font-black uppercase tracking-[0.2em] text-zs-text-muted">Sistema</span>
          </div>
          <NuxtLink to="/settings" 
            class="group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-fast relative"
            :class="isActive('/settings') ? 'bg-zs-blue/10 text-zs-blue-lt border border-zs-blue/20' : 'text-zs-text-secondary hover:bg-white/5 hover:text-zs-text-primary'">
            <UIcon name="i-heroicons-cog-6-tooth-20-solid" class="w-5 h-5 transition-transform duration-normal group-hover:scale-110" />
            <span class="text-sm font-semibold">Configuración</span>
            <div v-if="isActive('/settings')" class="absolute left-0 w-1 h-6 bg-zs-blue rounded-r-full shadow-zs-glow-blue"></div>
          </NuxtLink>
        </nav>

        <!-- User Footer -->
        <div class="p-4 border-t border-white/5 mt-auto">
          <div class="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-3 hover:border-white/10 transition-colors">
            <div class="w-10 h-10 rounded-xl bg-zs-gradient-brand flex items-center justify-center font-black text-white shadow-zs-glow-violet">
              {{ userInitial }}
            </div>
            <div class="flex-1 overflow-hidden">
              <div class="text-xs font-bold text-white truncate">{{ userName }}</div>
              <div class="text-[10px] text-zs-text-muted uppercase tracking-wider truncate">{{ companyName }}</div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col min-h-screen relative z-10">
        <!-- Topbar -->
        <header class="h-16 sticky top-0 bg-zs-bg-primary/40 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-8 z-[90]">
          <div class="flex items-center gap-6">
            <div class="lg:hidden w-10 h-10 rounded-xl border border-white/10 flex items-center justify-center">
              <Bars3Icon class="w-5 h-5" />
            </div>
            <div class="flex items-center gap-3">
              <div class="w-1 h-3 bg-zs-blue rounded-full"></div>
              <h1 class="text-[10px] font-black uppercase tracking-[0.4em] text-zs-text-muted">
                System Path: {{ currentPageTitle }}
              </h1>
            </div>
          </div>

          <div class="flex items-center gap-6">
            <!-- Global Search Placeholder -->
            <div class="hidden md:flex items-center gap-3 px-4 py-1.5 rounded-lg bg-white/5 border border-white/5 text-zs-text-muted">
              <span class="text-[10px] font-bold tracking-widest uppercase">Search System...</span>
              <kbd class="text-[9px] bg-white/10 px-1.5 py-0.5 rounded border border-white/10">⌘K</kbd>
            </div>
            
            <div class="flex items-center gap-3">
              <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span class="text-[9px] font-black uppercase tracking-widest text-emerald-500">Node Online</span>
            </div>
          </div>
        </header>

        <!-- Page Content -->
        <div class="flex-1 p-8 animate-cascade">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, defineComponent, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// ─── Nav items ──────────────────────────────────────────────
const navItems = [
  { to: '/',          label: 'Dashboard',  icon: 'i-heroicons-home-20-solid' },
  { to: '/invoices',  label: 'Facturas',   icon: 'i-heroicons-document-text-20-solid' },
  { to: '/clients',   label: 'Clientes',   icon: 'i-heroicons-users-20-solid' },
  { to: '/products',  label: 'Productos',  icon: 'i-heroicons-cube-20-solid' },
  { to: '/reports',   label: 'Reportes',   icon: 'i-heroicons-chart-bar-20-solid' },
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

</script>
