<!-- src/components/QeModal.vue -->
<template>
    <transition name="modal-fade">
        <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center">
            <div class="absolute inset-0 bg-black bg-opacity-40 backdrop-blur-sm transition-opacity duration-200"
                @click="$emit('update:modelValue', false)" />
            <transition name="modal-scale">
                <div class="relative bg-white dark:bg-qe-black2 rounded-2xl shadow-2xl max-w-sm w-full text-center px-6 py-7 z-2 flex flex-col gap-4 animate-pop-in"
                    v-if="modelValue">
                    <slot name="icon">
                        <div class="flex justify-center">
                            <svg class="w-12 h-12 text-red-500" fill="none" stroke="currentColor" stroke-width="2"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                    </slot>
                    <div class="font-semibold text-lg text-gray-800 dark:text-white">
                        <slot />
                    </div>
                    <div class="flex justify-center gap-4">
                        <button @click="$emit('confirm')" class="qe-btn-danger min-w-[110px]">
                            <slot name="confirm">Удалить</slot>
                        </button>
                        <button @click="$emit('update:modelValue', false)" class="qe-btn-secondary min-w-[110px]">
                            <slot name="cancel">Отмена</slot>
                        </button>
                    </div>
                </div>
            </transition>
        </div>
    </transition>
</template>

<script setup>
defineProps({
    modelValue: { type: Boolean, required: true }
})
defineEmits(['update:modelValue', 'confirm'])
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
    transition: opacity 0.18s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
    opacity: 0;
}

.modal-scale-enter-active {
    transition: transform 0.22s cubic-bezier(.56, .05, .4, 1.14), opacity 0.22s;
}

.modal-scale-enter-from {
    transform: scale(0.96);
    opacity: 0;
}

.modal-scale-enter-to {
    transform: scale(1);
    opacity: 1;
}

.modal-scale-leave-active {
    transition: transform 0.16s, opacity 0.16s;
}

.modal-scale-leave-from {
    transform: scale(1);
    opacity: 1;
}

.modal-scale-leave-to {
    transform: scale(0.98);
    opacity: 0;
}

.animate-pop-in {
    animation: pop-in 0.18s cubic-bezier(.56, .05, .4, 1.14);
}

@keyframes pop-in {
    from {
        transform: scale(0.96);
        opacity: 0;
    }

    to {
        transform: scale(1);
        opacity: 1;
    }
}
</style>
  
