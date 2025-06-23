<template>
    <div ref="root" class="relative">
        <div @click="toggle" class="qe-input w-full flex items-center cursor-pointer min-h-[40px] relative">
            <span class="truncate text-left">
                {{ selectedLabel || placeholder }}
            </span>
            <span
                class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none transition-transform duration-200"
                :class="{ 'rotate-180': open }">
                <ChevronDown class="w-4 h-4 text-gray-400" />
            </span>
        </div>
        <transition name="fade">
            <div v-if="open"
                class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 border border-gray-200 dark:border-qe-black2 rounded-xl shadow max-h-52 overflow-auto">
                <ul class="py-1">
                    <li v-for="opt in options" :key="opt.value" @click.stop="select(opt.value)"
                        class="px-3 py-2 flex items-center gap-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">
                        <span>{{ opt.label }}</span>
                        <span v-if="modelValue === opt.value" class="ml-auto text-blue-500">✓</span>
                    </li>
                </ul>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
    modelValue: [String, Number, null],
    options: { type: Array, default: () => [] },
    placeholder: { type: String, default: 'Выберите' }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const root = ref(null)
onClickOutside(root, () => (open.value = false))

const selectedLabel = computed(() => {
    const found = props.options.find(o => o.value === props.modelValue)
    return found?.label || ''
})

function toggle() {
    open.value = !open.value
}
function select(val) {
    emit('update:modelValue', val)
    open.value = false
}
</script>
