<script setup lang="ts">
import { SidebarTrigger } from '@/components/ui/sidebar'
import { useSidebar } from '@/components/ui/sidebar/utils'
import { computed } from 'vue'

const { state, isMobile } = useSidebar()
const triggerLeft = computed(() => {
  if (isMobile.value) return '0px'
  return state.value === 'expanded' ? 'var(--sidebar-width)' : '0px'
})
</script>

<template>
  <SidebarTrigger
    class="size-[40px] h-dvh fixed top-0 z-20 p-0 bg-gray-200 rounded-l-none flex transition-all duration-200"
    :style="{ left: triggerLeft }"
  />
</template>

