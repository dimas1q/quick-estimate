<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import Datepicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

// Поддержка dark/light через отслеживание <html class="dark">
const isDark = ref(document.documentElement.classList.contains('dark'))
onMounted(() => {
    const observer = new MutationObserver(() => {
        isDark.value = document.documentElement.classList.contains('dark')
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    onUnmounted(() => observer.disconnect())
})

const props = defineProps({
    modelValue: null,                 // v-model
    label: { type: String, default: '' },
    placeholder: { type: String, default: '' },
    format: { type: [Function, String], default: undefined }, // Можно прокинуть свою функцию форматирования
    locale: { type: [Object, String], default: 'ru' },
    inputClass: { type: String, default: 'qe-input' },
    enableTimePicker: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const innerValue = computed({
    get: () => props.modelValue,
    set: (v) => emit('update:modelValue', v),
})
</script>

<template>
    <div>
        <label v-if="label" class="text-sm text-gray-600 dark:text-gray-300">{{ label }}</label>
        <Datepicker v-model="innerValue" :locale="locale" :format="format" :dark="isDark" cancelText="Отмена"
            selectText="Выбрать" :placeholder="placeholder" :enable-time-picker="enableTimePicker"
            :input-class-name="inputClass" class="mt-2" style="width:100%;" />
    </div>
</template>
