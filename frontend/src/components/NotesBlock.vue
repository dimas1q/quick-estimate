<template>
  <div class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border dark:border-qe-black2 shadow-sm">
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-2">
        <NotebookPen class="w-6 h-6 text-blue-600" />
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white">Примечания</h3>
      </div>
      <button v-if="!adding" @click="startAdd" class="qe-btn">Добавить</button>
    </div>
    <div v-if="adding" class="mb-4 space-y-2">
      <textarea v-model="newText" rows="2" class="w-full qe-textarea" placeholder="Текст примечания" />
      <div class="flex justify-end gap-2">
        <button class="qe-btn-secondary" @click="cancelAdd">Отмена</button>
        <button class="qe-btn" @click="saveAdd">Сохранить</button>
      </div>
    </div>
    <div v-if="notes.length === 0 && !adding" class="text-sm text-gray-500">Нет примечаний</div>
    <div v-for="n in notes" :key="n.id" class="border-t dark:border-qe-black2 pt-4 mt-4">
      <div v-if="editId === n.id" class="space-y-2">
        <textarea v-model="editText" rows="2" class="w-full qe-textarea" />
        <div class="flex justify-end gap-2">
          <button class="qe-btn-secondary" @click="cancelEdit">Отмена</button>
          <button class="qe-btn" @click="saveEdit(n.id)">Сохранить</button>
        </div>
      </div>
      <div v-else class="flex justify-between items-start gap-3">
        <div class="flex-1">
          <p class="whitespace-pre-line">{{ n.text }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ formatDate(n.created_at) }}<span v-if="n.updated_at"> (обновлено {{ formatDate(n.updated_at) }})</span> • {{ n.user_name }}</p>
        </div>
        <div class="flex gap-2 whitespace-nowrap">
          <button class="qe-btn-warning px-2 py-1" @click="startEdit(n)"><LucidePencil class="w-4 h-4" /></button>
          <button class="qe-btn-danger px-2 py-1" @click="emit('delete', n.id)"><LucideTrash2 class="w-4 h-4" /></button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NotebookPen, LucidePencil, LucideTrash2 } from 'lucide-vue-next'

const props = defineProps({
  notes: { type: Array, default: () => [] }
})
const emit = defineEmits(['add', 'update', 'delete'])

const adding = ref(false)
const newText = ref('')
function startAdd() { adding.value = true; newText.value = '' }
function cancelAdd() { adding.value = false }
function saveAdd() { emit('add', newText.value); adding.value = false }

const editId = ref(null)
const editText = ref('')
function startEdit(n) { editId.value = n.id; editText.value = n.text }
function cancelEdit() { editId.value = null }
function saveEdit(id) { emit('update', { id, text: editText.value }); editId.value = null }

function formatDate(d) { return new Date(d).toLocaleString() }
</script>
