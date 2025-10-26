<script setup lang="ts">
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
</script>

<template>
  <div class="w-full h-dvh">
    <SidebarProvider>
        <AppSidebar />
        <SidebarTrigger class="size-[40px] p-0 bg-gray-200 h-dvh rounded-l-none flex "/>
        <slot />
    </SidebarProvider>
  </div>
</template>