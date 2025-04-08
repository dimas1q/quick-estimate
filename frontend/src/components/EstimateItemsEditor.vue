<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Услуги</h2>
    
    <div class="grid grid-cols-7 gap-2 font-semibold text-sm text-gray-600">
      <div>Название</div>
      <div>Описание</div>
      <div>Кол-во</div>
      <div>Ед. изм.</div>
      <div>Цена</div>
      <div>Скидка</div>
      <div></div>
    </div>

    <div v-for="(item, index) in items" :key="index" class="grid grid-cols-7 gap-2 items-end">
      <input v-model="item.name" placeholder="Название" class="input" />
      <input v-model="item.description" placeholder="Описание" class="input" />
      <input v-model.number="item.quantity" type="number" class="input" placeholder="Кол-во" />
      <input v-model="item.unit" class="input" placeholder="Ед. изм." />
      <input v-model.number="item.unit_price" type="number" class="input" placeholder="Цена" />
      <input v-model.number="item.discount" type="number" class="input" placeholder="Скидка" />
      <button @click="removeItem(index)" class="text-red-600 hover:underline">Удалить</button>
    </div>

    <button @click="addItem" class="bg-gray-200 px-3 py-1 rounded">+ Добавить строку</button>
  </div>
</template>

<script setup>
import { reactive, watch, defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: Array
})

const emit = defineEmits(['update:modelValue'])

const items = reactive(props.modelValue || [])

watch(items, () => {
  emit('update:modelValue', items)
}, { deep: true })

function addItem() {
  items.push({
    name: '',
    description: '',
    quantity: 1,
    unit: 'шт',
    unit_price: 0,
    discount: 0,
    discount_type: 'percent',
    category: ''
  })
}

function removeItem(index) {
  items.splice(index, 1)
}
</script>

<style scoped>
.input {
  @apply border p-2 rounded text-sm w-full;
}
</style>
