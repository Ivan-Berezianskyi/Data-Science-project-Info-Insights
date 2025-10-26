<script setup lang="ts">
import {
  Card,
  CardHeader,
  CardTitle,
  CardFooter,
  CardContent,
} from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { useMediaQuery } from "@vueuse/core";

const isOn = ref(false);
const isMobile = useMediaQuery("(max-width: 768px)");

// Show buttons on mobile or when hovered on desktop
const shouldShowButtons = computed(() => isMobile.value || isOn.value);
const isFileDialogOpen = inject<Ref<boolean>>("isNotebookFileDialogOpen");

const handleAddFile = () => {
  if (isFileDialogOpen) {
    isFileDialogOpen.value = true;
  }
};
</script>
<template>
    <Card @mouseenter="isOn = true" @mouseleave="isOn = false" class="w-52 h-fit relative">
      <CardHeader>
        <CardTitle> Name </CardTitle>
      </CardHeader>
      <CardContent :class="isMobile ? 'pb-20' : 'pb-4'">
        <p class="text-wrap">
          Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestias
          expedita saepe vitae dolor...
        </p>
      </CardContent>
      <div :class="shouldShowButtons ? '' : 'opacity-0'" class="transition-opacity duration-500 absolute bottom-0 rounded-b-lg w-full px-3 sm:px-8 pb-2 pt-12 flex flex-col sm:flex-row gap-y-1 sm:gap-y-0 sm:gap-x-1 justify-center bg-gradient-to-t from-gray-200 to-transparent">
        <Button @click="handleAddFile" class=" w-full sm:w-[80%]">Add File</Button>
        <Button class="w-full sm:w-fit" variant="destructive"
          ><Icon size="30px" name="material-symbols:delete-forever-outline-rounded"></Icon
        ></Button>
      </div>
    </Card>
</template>