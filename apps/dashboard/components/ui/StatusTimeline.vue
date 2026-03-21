<template>
  <div class="space-y-6 relative before:absolute before:inset-0 before:left-3 before:w-0.5 before:bg-white/5 before:rounded-full">
    <div v-for="(item, index) in steps" :key="index" 
         class="flex gap-6 group animate-zs-fade-up"
         :style="{ animationDelay: `${index * 0.1}s` }">
      
      <!-- Dot -->
      <div class="relative z-10 w-6 h-6 flex items-center justify-center shrink-0">
        <div v-if="item.status === 'done'" 
             class="w-3 h-3 rounded-full bg-zs-emerald shadow-zs-glow-emerald border-2 border-zs-bg-primary"></div>
        <div v-else-if="item.status === 'active'" 
             class="w-3 h-3 rounded-full bg-zs-blue shadow-zs-glow-blue border-2 border-zs-bg-primary animate-pulse"></div>
        <div v-else 
             class="w-2.5 h-2.5 rounded-full bg-zs-text-muted/20 border-2 border-zs-bg-primary"></div>
      </div>

      <!-- Content -->
      <div class="flex-grow pb-8 border-b border-white/5 last:border-0">
        <div class="flex items-center justify-between mb-1">
          <h4 class="text-xs font-black uppercase tracking-widest"
              :class="item.status === 'done' ? 'text-white' : item.status === 'active' ? 'text-zs-blue-lt' : 'text-zs-text-muted'">
            {{ item.title }}
          </h4>
          <span class="text-[10px] font-bold text-zs-text-muted group-hover:text-zs-text-secondary transition-colors">
            {{ item.time }}
          </span>
        </div>
        <p class="text-[11px] leading-relaxed"
           :class="item.status === 'done' ? 'text-zs-text-secondary' : 'text-zs-text-muted'">
          {{ item.description }}
        </p>

        <!-- Code/XML snippet if exists -->
        <div v-if="item.code" class="mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/5 group-hover:border-white/10 transition-all font-mono text-[10px] text-zs-text-secondary break-all">
          {{ item.code }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface TimelineStep {
  title: string
  description: string
  time: string
  status: 'done' | 'active' | 'pending'
  code?: string
}

defineProps<{
  steps: TimelineStep[]
}>()
</script>
