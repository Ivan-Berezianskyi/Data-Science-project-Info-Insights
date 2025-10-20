<script setup lang="ts">
import { Textarea } from '~/components/ui/textarea';
import { Button } from '~/components/ui/button';
</script>

<template>
    <div class="w-full h-dvh flex justify-center items-center">
        <div class="flex flex-col justify-center items-center w-1/2 gap-y-4">
            <p class="text-2xl font-bold">Дай Боже здоровʼя!</p>
            <div class="flex items-end w-full border-1 rounded-lg p-1 h-24">
                <Textarea class="h-full resize-none" placeholder="Початимся?"/>
                <button class="p-1 flex justify-center items-center bg-gray-300 hover:bg-gray-200 transition-colors duration-150 rounded-lg"><Icon size="30px" name="material-symbols:mode-comment-outline"/></button>
            </div>
            
        </div>

    </div>
</template>