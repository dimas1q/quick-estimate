<!-- components/Modal.vue -->
<template>
    <div class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50" @click.self="close">
        <div class="bg-white rounded-xl p-6 min-w-[320px] max-w-xl shadow-2xl transition-all"
            :style="{ minHeight: '320px' }">
            <slot />
        </div>
    </div>
</template>
<script setup>
const emit = defineEmits(['close'])
function close() { emit('close') }
</script>
  
