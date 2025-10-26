<script setup lang="ts">
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

import { Button } from './ui/button';

const isOpen = inject<Ref<boolean>>("isNotebookFileDialogOpen");

const openValue = computed(() => isOpen?.value ?? false);

const updateOpen = (value: boolean) => {
  if (isOpen) {
    isOpen.value = value;
  }
};

const handleClose = () => {
  if (isOpen) {
    isOpen.value = false;
  }
};
</script>

<template>
    <Dialog :open="openValue" @update:open="updateOpen">
        <DialogContent>
            <DialogHeader>
                <DialogTitle>
                    Add File
                </DialogTitle>
                <DialogDescription>
                    Upload files to add to your notebook
                </DialogDescription>
            </DialogHeader>
            <div class="w-full h-32 border-dashed border-2 rounded-lg hover:bg-gray-200 transition-colors duration-150  border-gray-300 flex justify-center items-center"><p>Drop your files here</p></div>
            <DialogFooter>
                <Button @click="handleClose">Add</Button>
                <Button @click="handleClose" variant="outline">Cancel</Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
</template>