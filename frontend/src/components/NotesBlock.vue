<template>
  <div class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border border-gray-200 dark:border-qe-black2 shadow-sm">
    <div class="flex justify-between items-center mb-2 border-b border-gray-200 dark:border-qe-black2 pb-4">
      <div class="flex items-center gap-2">
        <NotebookPen class="w-6 h-6 text-blue-600" />
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white select-none">Примечания</h3>
      </div>
      <button v-if="!adding" @click="startAdd" class="qe-btn shadow-sm transition-all">Добавить</button>
    </div>
    <!-- Добавление примечания -->
    <Transition name="note-fade">
      <div v-if="adding" class="mb-4 space-y-2" key="add-note">
        <textarea v-model="newText" rows="2" ref="addInput"
          class="w-full qe-textarea rounded-xl bg-gray-50 focus:bg-white border border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all"
          placeholder="Текст примечания" />
        <div class="flex justify-end gap-2">
          <button class="qe-btn-secondary" @click="cancelAdd">Отмена</button>
          <button class="qe-btn" :disabled="!newText.trim()" @click="saveAdd">Сохранить</button>
        </div>
      </div>
    </Transition>
    <TransitionGroup name="note-fade" tag="div">
      <div v-for="(n, i) in notes" :key="n.id" :class="[
        'pt-4',
        i !== 0 ? 'border-t border-gray-200 dark:border-qe-black2 mt-4' : 'mt-0',
      ]">
        <Transition name="note-fade">
          <div v-if="editId === n.id" class="space-y-2" key="edit-note">
            <textarea v-model="editText" ref="editInput" rows="2"
              class="w-full qe-textarea rounded-xl bg-gray-50 focus:bg-white border border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all" />
            <div class="flex justify-end gap-2">
              <button class="qe-btn-secondary" @click="cancelEdit">Отмена</button>
              <button class="qe-btn" :disabled="!editText.trim()" @click="saveEdit(n.id)">Сохранить</button>
            </div>
          </div>
          <div v-else class="flex justify-between items-start gap-3" key="display-note">
            <div class="flex-1">
              <p class="whitespace-pre-line text-gray-900 dark:text-gray-100">{{ n.text }}</p>
              <p class="text-xs text-gray-500 mt-1">
                {{ formatDate(n.created_at) }}
                <span v-if="n.updated_at">
                  (обновлено {{ formatDate(n.updated_at) }})
                </span>
                • {{ n.user_name }}
              </p>
            </div>
            <div class="flex gap-2 whitespace-nowrap mt-3">
              <button
                class="qe-btn-warning px-2 py-1 rounded-full hover:bg-yellow-500 dark:hover:bg-yellow-900/20 transition"
                @click="startEdit(n)" aria-label="Редактировать">
                <LucidePencil class="w-4 h-4" />
              </button>
              <button class="qe-btn-danger px-2 py-1 rounded-full hover:bg-red-700 dark:hover:bg-red-900/20 transition"
                @click="emit('delete', n.id)" aria-label="Удалить">
                <LucideTrash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </TransitionGroup>
    <div v-if="notes.length === 0 && !adding" class="text-sm text-gray-500 pt-2">Нет примечаний</div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { NotebookPen, LucidePencil, LucideTrash2 } from 'lucide-vue-next'

const props = defineProps({
  notes: { type: Array, default: () => [] }
})
const emit = defineEmits(['add', 'update', 'delete'])

const adding = ref(false)
const newText = ref('')
const addInput = ref(null)
function startAdd() {
  adding.value = true
  newText.value = ''
  nextTick(() => addInput.value?.focus())
}
function cancelAdd() { adding.value = false }
function saveAdd() {
  if (!newText.value.trim()) return
  emit('add', newText.value.trim())
  adding.value = false
}

const editId = ref(null)
const editText = ref('')
const editInput = ref(null)
function startEdit(n) {
  editId.value = n.id
  editText.value = n.text
  nextTick(() => editInput.value?.focus())
}
function cancelEdit() { editId.value = null }
function saveEdit(id) {
  if (!editText.value.trim()) return
  emit('update', { id, text: editText.value.trim() })
  editId.value = null
}

function formatDate(d) { return new Date(d).toLocaleString() }
</script>

<style scoped>
.note-fade-enter-active,
.note-fade-leave-active,


.note-fade-enter-from,
.note-fade-leave-to {
  opacity: 0;
}
</style>
