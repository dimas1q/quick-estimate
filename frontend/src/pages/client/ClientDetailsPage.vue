<template>
  <div class="py-8 max-w-6xl mx-auto">
    <div v-if="!client" class="text-center py-10 text-lg text-gray-500 dark:text-gray-400">
      Загрузка…
    </div>
    <div v-else class="space-y-6">
      <!-- Шапка и кнопки -->
      <div class="flex justify-between items-center pb-2 mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 dark:text-white">
            Клиент: {{ client.name }}
          </h1>
        </div>
        <div class="flex space-x-2 items-center">
          <RouterLink :to="`/clients/${client.id}/edit`" class="qe-btn-warning">
            Редактировать
          </RouterLink>
          <button @click="confirmDelete" class="qe-btn-danger">Удалить</button>
        </div>
      </div>

      <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 mb-6 w-fit">
        <button :class="[
          'px-5 py-2 rounded-lg text-sm font-semibold transition',
          activeTab === 'details'
            ? 'bg-white dark:bg-gray-900 text-blue-600 shadow'
            : 'text-gray-500 hover:text-blue-600',
        ]" @click="activeTab = 'details'">
          Сведения
        </button>
        <button :class="[
          'px-5 py-2 rounded-lg text-sm font-semibold transition',
          activeTab === 'history'
            ? 'bg-white dark:bg-gray-900 text-blue-600 shadow'
            : 'text-gray-500 hover:text-blue-600',
        ]" @click="activeTab = 'history'">
          История
        </button>
      </div>

      <!-- Блок данных — такой же стиль как у сметы -->
      <div class="grid gap-3 text-sm text-gray-800 dark:text-gray-200" v-if="activeTab === 'details'">
        <div
          class="grid grid-cols-2 gap-4 shadow-sm border dark:border-qe-black2 bg-white dark:bg-qe-black3 rounded-2xl p-6">
          <p><strong>Компания:</strong> {{ client.company || "—" }}</p>

          <p><strong>Расчетный счет:</strong> {{ client.account || "—" }}</p>
          <p><strong>Email:</strong> {{ client.email || "—" }}</p>
          <p><strong>Корр. счет:</strong> {{ client.corr_account || "—" }}</p>

          <p>
            <strong>Фактический адрес:</strong>
            {{ client.actual_address || "—" }}
          </p>
          <p><strong>ИНН:</strong> {{ client.inn || "—" }}</p>
          <p>
            <strong>Юридический адрес:</strong>
            {{ client.legal_address || "—" }}
          </p>

          <p><strong>БИК:</strong> {{ client.bik || "—" }}</p>
          <p><strong>Телефон:</strong> {{ client.phone || "—" }}</p>
          <p><strong>КПП:</strong> {{ client.kpp || "—" }}</p>
          <p><strong>Примечания:</strong> {{ client.notes || "—" }}</p>
          <p><strong>Банк:</strong> {{ client.bank || "—" }}</p>
        </div>
      </div>

      <!-- Сметы клиента -->
      <div v-if="activeTab === 'details'"
        class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-sm p-6 mt-6">
        <h2 class="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
          Сметы клиента
        </h2>
        <div v-if="estimates.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="e in estimates" :key="e.id"
            class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 p-4 rounded-xl shadow-sm flex flex-col gap-2 hover:shadow-md transition">
            <div class="flex justify-between items-center">
              <RouterLink :to="`/estimates/${e.id}`" class="font-semibold">
                {{ e.name }}
              </RouterLink>
              <span class="text-gray-500 text-xs">{{
                new Date(e.date).toLocaleDateString()
              }}</span>
            </div>
          </div>
        </div>
        <div v-else
          class="text-center text-gray-500 border border-gray-200 dark:border-qe-black2 p-4 rounded-2xl py-8 mt-2 bg-white dark:bg-qe-black3">
          Сметы отсутствуют.
        </div>
      </div>

      <div v-if="activeTab === 'history'" class="mt-6">
        <h2 class="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
          История клиента
        </h2>
        <div v-if="logs.length"
          class="rounded-xl border border-gray-200 dark:border-qe-black2 dark:bg-qe-black3 bg-white dark:bg-gray-900 divide-y dark:divide-qe-black2 shadow-sm">
          <!-- Заголовок -->
          <div
            class="flex items-center px-5 py-2 bg-gray-50 dark:bg-qe-black2 rounded-t-xl font-medium text-gray-700 dark:text-gray-200">
            <div class="w-40 shrink-0">Дата</div>
            <div class="flex-1">Событие</div>
            <div class="w-[140px] shrink-0 text-right pr-4">Детали</div>
          </div>
          <!-- Логи -->
          <div v-for="log in logs" :key="log.id" class="px-5 py-2 group">
            <div class="flex items-center">
              <div class="w-40 text-sm text-gray-400 shrink-0">
                {{ new Date(log.timestamp).toLocaleString() }}
              </div>
              <div class="flex-1 flex items-center gap-2 min-w-0">
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
                  {{ log.description }}
                </span>
                <span class="text-sm text-gray-500 truncate">— {{ log.user_name || '-' }}</span>
              </div>
              <div class="w-[140px] shrink-0 text-right pr-4 flex justify-end">
                <button v-if="log.details && log.details.length" @click="toggleDetails(log.id)"
                  class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded text-blue-600 hover:bg-blue-50 transition truncate">
                  <span>{{ showDetails[log.id] ? 'Скрыть детали' : 'Детали' }}</span>
                  <svg :class="['w-4 h-4 transition-transform', showDetails[log.id] ? 'rotate-180' : '']" fill="none"
                    stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </button>
              </div>
            </div>
            <transition name="fade">
              <ul v-if="log.details && log.details.length && showDetails[log.id]"
                class="mt-2 pl-2 border-l dark:border-qe-black2 border-blue-200 text-sm space-y-1">
                <li v-for="(d, i) in log.details" :key="i" class="text-blue-700 dark:text-blue-500">
                  {{ d }}
                </li>
              </ul>
            </transition>
          </div>
        </div>
        <div v-else class="text-gray-500">Записей нет.</div>
      </div>

    </div>

    <!-- Модалка подтверждения удаления -->
    <QeModal v-model="showConfirm" @confirm="deleteClient">
      Вы уверены, что хотите удалить данного клиента?
      <template #confirm>Удалить</template>
      <template #cancel>Отмена</template>
    </QeModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useClientsStore } from "@/store/clients";
import { useToast } from "vue-toastification";
import QeModal from "@/components/QeModal.vue";

const route = useRoute();
const router = useRouter();
const client = ref(null);
const estimates = ref([]);
const logs = ref([]);
const activeTab = ref("details");
const showConfirm = ref(false);
const store = useClientsStore();
const toast = useToast();
const showDetails = ref({})

onMounted(async () => {
  const { client: c, estimates: e } = await store.getClientWithEstimates(
    route.params.id,
  );
  client.value = c;
  estimates.value = e;
  logs.value = await store.getClientLogs(route.params.id);
});

function confirmDelete() {
  showConfirm.value = true;
}

function toggleDetails(id) {
  showDetails.value[id] = !showDetails.value[id]
}

async function deleteClient() {
  try {
    await store.deleteClient(route.params.id);
    toast.success("Клиент удален");
    router.push("/clients");
  } catch (e) {
    if (e.response?.data?.detail) {
      toast.error(e.response.data.detail);
    } else {
      toast.error("Ошибка удаления клиента");
    }
  }
}
</script>
