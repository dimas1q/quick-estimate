<!-- frontend/src/components/MetricCard.vue -->
<template>
    <div class="bg-gray p-4 rounded-lg shadow flex items-center space-x-3" :title="title">
        <!-- Здесь рендерим компонент-иконку -->
        <div class="text-2xl">
            <component :is="icon" class="w-6 h-6" />
        </div>
        <div>
            <div class="text-sm text-gray-500">{{ title }}</div>
            <div class="text-xl font-semibold">
                {{ displayValue }}<span v-if="suffix">{{ suffix }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    title: { type: String, required: true },
    value: { type: [Number, String], required: true },
    suffix: { type: String, default: '' },
    icon: { type: [Object, Function], required: true },
    isPercent: { type: Boolean, default: false },
})

const displayValue = computed(() => {
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
</script>
