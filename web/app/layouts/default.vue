<script setup lang="ts">
import { SidebarProvider } from '@/components/ui/sidebar'
</script>

<template>
  <div class="w-full h-dvh">
    <SidebarProvider>
      <AppSidebar />
      <FixedSidebarTrigger />
      <slot />
    </SidebarProvider>
  </div>
</template>