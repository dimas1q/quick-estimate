<script setup>
import { computed } from 'vue'

const props = defineProps({
    title: { type: String, required: true },
    value: { type: [Number, String, null], required: true },
    suffix: { type: String, default: '' },
    icon: { type: [Object, Function], required: true },
    isPercent: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
})

const displayValue = computed(() => {
    if (props.value === null || props.value === undefined || props.value === '') {
        return '—'
    }
    if (props.isPercent && typeof props.value === 'number') {
        return props.value.toFixed(2)
    }
    if (typeof props.value === 'number') {
        return new Intl.NumberFormat('ru-RU', {
            style: 'decimal', minimumFractionDigits: 0
        }).format(props.value)
    }
    return props.value
})

const showSuffix = computed(() => {
    // Показываем суффикс только если есть нормальное значение
    return displayValue.value !== '—' && props.suffix
})
</script>

<template>
    <div class="bg-white dark:bg-qe-black border border-gray-200 dark:border-gray-800 p-5 rounded-xl shadow flex items-center space-x-3 min-h-[94px]"
        :class="{ 'opacity-50': disabled }" :title="title">
        <div class="text-2xl">
            <component :is="icon" class="w-6 h-6" />
        </div>
        <div>
            <div class="text-sm text-gray-500">{{ title }}</div>
            <div class="text-xl font-semibold flex items-center gap-1">
                {{ displayValue }}
                <span v-if="showSuffix" class="text-base">{{ suffix }}</span>
            </div>
        </div>
    </div>
</template>
