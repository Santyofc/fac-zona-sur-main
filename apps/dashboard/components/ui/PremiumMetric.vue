<template>
  <div class="zs-card group flex flex-col p-8 min-h-[220px] transition-all duration-normal relative overflow-hidden"
       :class="[
         accent === 'blue' ? 'hover:shadow-zs-glow-blue' :
         accent === 'emerald' ? 'hover:shadow-zs-glow-emerald' :
         accent === 'amber' ? 'hover:shadow-zs-glow-amber' :
         accent === 'rose' ? 'hover:shadow-zs-glow-rose' : 'hover:shadow-zs-glow-violet'
       ]">
    
    <!-- Header -->
    <div class="flex justify-between items-start relative z-10">
      <div class="space-y-1">
        <p class="text-[10px] font-black uppercase tracking-[0.25em] text-zs-text-muted group-hover:text-zs-text-secondary transition-colors">
          {{ label }}
        </p>
        <h3 class="text-4xl font-black tracking-tighter text-white group-hover:scale-105 origin-left transition-transform duration-normal">
          {{ value }}
        </h3>
      </div>
      <div class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:rotate-12 group-hover:border-white/20 transition-all duration-normal shadow-zs-card">
        <slot name="icon">
          <UIcon :name="icon" class="w-6 h-6" :class="iconClass" />
        </slot>
      </div>
    </div>

    <!-- Trend -->
    <div v-if="trend" class="mt-4 flex items-center gap-2 relative z-10">
      <div class="flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-black"
           :class="trend > 0 ? 'bg-zs-emerald/10 text-zs-emerald border border-zs-emerald/20' : 'bg-zs-rose/10 text-zs-rose border border-zs-rose/20'">
        <span>{{ trend > 0 ? '↑' : '↓' }}</span>
        <span>{{ Math.abs(trend) }}%</span>
      </div>
      <span class="text-[10px] text-zs-text-muted font-bold uppercase tracking-wider">vs periodo anterior</span>
    </div>

    <div class="flex-grow"></div>

    <!-- Background Visualization (Animated SVG) -->
    <div class="absolute bottom-0 left-0 w-full h-24 opacity-10 group-hover:opacity-25 transition-opacity">
      <svg class="w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
        <path :d="pathData" 
              fill="none" 
              :stroke="strokeColor" 
              stroke-width="2" 
              class="path-animation" />
        <linearGradient :id="'gradient-' + accent" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="strokeColor" stop-opacity="0.4" />
          <stop offset="100%" :stop-color="strokeColor" stop-opacity="0" />
        </linearGradient>
        <path :d="areaData" :fill="'url(#gradient-' + accent + ')'" />
      </svg>
    </div>

    <!-- Glow Orb -->
    <div class="absolute -bottom-12 -right-12 w-32 h-32 rounded-full blur-[50px] opacity-0 group-hover:opacity-10 transition-opacity"
         :class="bgGlowClass"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  label: string
  value: string | number
  icon?: string
  accent?: 'blue' | 'emerald' | 'violet' | 'amber' | 'rose'
  trend?: number
}

const props = withDefaults(defineProps<Props>(), {
  accent: 'blue',
  icon: 'i-heroicons-chart-bar'
})

const iconClass = computed(() => {
  const map = {
    blue: 'text-zs-blue-lt',
    emerald: 'text-zs-emerald',
    violet: 'text-zs-violet',
    amber: 'text-zs-amber',
    rose: 'text-zs-rose'
  }
  return map[props.accent]
})

const strokeColor = computed(() => {
  const map = {
    blue: '#3b82f6',
    emerald: '#10b981',
    violet: '#8b5cf6',
    amber: '#f59e0b',
    rose: '#f43f5e'
  }
  return map[props.accent]
})

const bgGlowClass = computed(() => {
  const map = {
    blue: 'bg-zs-blue',
    emerald: 'bg-zs-emerald',
    violet: 'bg-zs-violet',
    amber: 'bg-zs-amber',
    rose: 'bg-zs-rose'
  }
  return map[props.accent]
})

// Simulated path data for the background
const points = Array.from({ length: 10 }, (_, i) => ({
  x: i * 45,
  y: 40 + Math.random() * 50
}))

const pathData = computed(() => {
  return `M ${points.map(p => `${p.x},${p.y}`).join(' L')}`
})

const areaData = computed(() => {
  return `${pathData.value} L 400,100 L 0,100 Z`
})
</script>

<style scoped>
.path-animation {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: dash 3s ease-in-out infinite alternate;
}

@keyframes dash {
  from { stroke-dashoffset: 1000; }
  to { stroke-dashoffset: 0; }
}
</style>
