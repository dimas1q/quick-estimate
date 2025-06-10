<template>
  <div class="py-8 max-w-6xl mx-auto">
    <div v-if="!client" class="text-center py-10 text-lg text-gray-500 dark:text-gray-400">
      Загрузка…
    </div>
    <div v-else class="space-y-7">
      <!-- Шапка -->
      <div class="flex flex-wrap justify-between items-center gap-4 pb-1 mb-7">
        <div class="flex items-center gap-2">
          <LucideUserRound class="w-10 h-10 text-blue-600" />
          <div>
            <h1 class="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
              <span>Клиент:</span>
              <span>{{ client.name }}</span>
            </h1>
          </div>
        </div>
        <div class="flex space-x-2 items-center">
          <RouterLink :to="`/clients/${client.id}/edit`" class="qe-btn-warning flex items-center">
            <LucidePencilLine class="w-4 h-4 mr-1" />
            <span>Редактировать</span>
          </RouterLink>
          <button @click="confirmDelete" class="qe-btn-danger flex items-center">
            <LucideTrash2 class="w-4 h-4 mr-1" />
            <span>Удалить</span>
          </button>
        </div>
      </div>

      <!-- Табы -->
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

      <!-- Данные клиента -->
      <div v-if="activeTab === 'details'">
        <div class="grid gap-4 text-sm text-gray-800 dark:text-gray-200 grid-cols-1 md:grid-cols-2">
          <!-- Левый блок -->
          <div
            class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border dark:border-qe-black2 shadow-sm space-y-2 h-full ">
            <div class="flex items-center mt-2">
              <LucideUserCircle class="w-5 h-5 text-blue-500 mr-2" />
              <span class="font-semibold mr-1">Контактное лицо:</span>
              <span>{{ client.name }}</span>
            </div>
            <div v-if="client.company" class="flex items-center ">
              <LucideBuilding2 class="w-5 h-5 text-pink-500 mr-2" />
              <span class="font-semibold mr-1">Компания:</span>
              <span>{{ client.company }}</span>
            </div>
            <div v-if="client.email" class="flex items-center ">
              <LucideMail class="w-5 h-5 text-green-600 mr-2" />
              <span class="font-semibold mr-1">Email:</span>
              <span>{{ client.email }}</span>
            </div>
            <div v-if="client.phone" class="flex items-center ">
              <LucidePhone class="w-5 h-5 text-yellow-500 mr-2" />
              <span class="font-semibold mr-1">Телефон:</span>
              <span>{{ client.phone }}</span>
            </div>
            <div v-if="client.actual_address" class="flex items-center ">
              <LucideMapPin class="w-5 h-5 text-indigo-500 mr-2" />
              <span class="font-semibold mr-1">Факт. адрес:</span>
              <span>{{ client.actual_address }}</span>
            </div>
            <div v-if="client.legal_address" class="flex items-center ">
              <LucideMap class="w-5 h-5 text-purple-500 mr-2" />
              <span class="font-semibold mr-1">Юр. адрес:</span>
              <span>{{ client.legal_address }}</span>
            </div>
            <div v-if="client.notes" class="flex items-center ">
              <LucideNotebookPen class="w-5 h-5 text-gray-400 mr-2" />
              <span class="font-semibold mr-1">Примечания:</span>
              <span>{{ client.notes }}</span>
            </div>
          </div>
          <!-- Правый блок -->
          <div
            class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border dark:border-qe-black2 shadow-sm space-y-2 h-full">
            <div class="flex items-center mb-4">
              <span class="text-lg font-bold">Реквизиты</span>
            </div>
            <div class="space-y-2">
              <div class="flex items-center">
                <LucideWallet class="w-5 h-5 text-blue-500 mr-2" />
                <span class="font-semibold mr-1">Рассч. счет:</span>
                <span>{{ client.account || "—" }}</span>
              </div>
              <div class="flex items-center">
                <LucideWallet class="w-5 h-5 text-blue-500 mr-2" />
                <span class="font-semibold mr-1">Корр. счет:</span>
                <span>{{ client.corr_account || "—" }}</span>
              </div>
              <div class="flex items-center">
                <LucideScanBarcode class="w-5 h-5 text-yellow-500 mr-2" />
                <span class="font-semibold mr-1">ИНН:</span>
                <span>{{ client.inn || "—" }}</span>
              </div>
              <div class="flex items-center">
                <LucideScanBarcode class="w-5 h-5 text-yellow-500 mr-2" />
                <span class="font-semibold mr-1">КПП:</span>
                <span>{{ client.kpp || "—" }}</span>
              </div>
              <div class="flex items-center">
                <LucideScanBarcode class="w-5 h-5 text-blue-400 mr-2" />
                <span class="font-semibold mr-1">БИК:</span>
                <span>{{ client.bik || "—" }}</span>
              </div>
              <div class="flex items-center">
                <LucideBanknote class="w-5 h-5 text-green-700 mr-2" />
                <span class="font-semibold mr-1">Банк:</span>
                <span>{{ client.bank || "—" }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Сметы клиента -->
      <div v-if="activeTab === 'details'"
        class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-sm p-6 ">
        <div class="flex items-center gap-2 mb-5">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-white">
            Сметы клиента
          </h2>
        </div>
        <div v-if="estimates.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="e in estimates" :key="e.id"
            class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 p-4 rounded-xl shadow-sm flex flex-col gap-2 hover:shadow-md transition">
            <div class="flex justify-between items-center">
              <RouterLink :to="`/estimates/${e.id}`"
                class="flex items-center gap-2 font-semibold text-blue-700 dark:text-blue-400 hover:underline">
                <LucideFileText class="w-5 h-5" /> {{ e.name }}
              </RouterLink>
              <span class="text-gray-500 text-xs flex items-center gap-1">
                <LucideCalendar class="w-4 h-4" />
                <span>{{ new Date(e.date).toLocaleDateString() }}</span>
              </span>
            </div>
          </div>
        </div>
        <QePagination
          :total="estimatesPagination.total"
          :limit="estimatesPagination.limit"
          :offset="estimatesPagination.offset"
          @update:page="changeEstPage"
          @update:limit="changeEstLimit"
        />
        <div v-else
          class="text-center text-gray-500 border border-gray-200 dark:border-qe-black2 p-4 rounded-2xl py-8 mt-2 bg-white dark:bg-qe-black3">
          <LucideAlertCircle class="w-5 h-5 text-yellow-400 inline-block mr-1" />
          Сметы отсутствуют.
        </div>
      </div>

      <!-- История изменений -->
      <div v-if="activeTab === 'history'" class="mt-6">
        <h2 class="text-sm font-semibold mb-4 text-gray-800 dark:text-white flex items-center gap-3">
          <span class="flex items-center justify-center gap-1">
            <LucideHistory class="w-5 h-5 text-blue-600" />
            <span>История клиента</span>
          </span>

        </h2>
        <div v-if="logs.length"
          class="rounded-xl border border-gray-200 dark:border-qe-black2 dark:bg-qe-black3 bg-white dark:bg-gray-900 divide-y dark:divide-qe-black2 shadow-sm">
          <!-- Заголовок -->
          <div
            class="flex items-center px-5 py-2 bg-gray-50 dark:bg-qe-black2 rounded-t-xl font-medium text-gray-700 dark:text-gray-200">
            <div class="w-40 shrink-0">Дата</div>
            <div class="flex-1">Событие</div>
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
                  class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded text-blue-600 hover:bg-blue-50 transition -mr-6">
                  <span>{{ showDetails[log.id] ? 'Скрыть детали' : 'Детали' }}</span>
                  <LucideChevronDown
                    :class="['w-4 h-4 transition-transform', showDetails[log.id] ? 'rotate-180' : '']" />
                </button>
              </div>
            </div>
            <transition name="fade">
              <ul v-if="log.details && log.details.length && showDetails[log.id]"
                class="mt-2 mb-2 pl-2 border-l dark:border-qe-black2 border-blue-200 text-sm space-y-1">
                <li v-for="(d, i) in log.details" :key="i" class="text-blue-700 dark:text-blue-500">
                  <template v-if="typeof d === 'object' && d.label">
                    <span class="font-semibold">{{ d.label }}:</span>
                    <span class="mx-1 text-gray-500 line-through">{{ d.old }}</span>
                    <span class="-mx-1 -mr-2 text-blue-700 dark:text-blue-400 font-semibold">→ {{ d.new }}</span>
                  </template>
                  <template v-else>
                    {{ d }}
                  </template>
                </li>
              </ul>
            </transition>
          </div>
        </div>
        <QePagination
          :total="logsPagination.total"
          :limit="logsPagination.limit"
          :offset="logsPagination.offset"
          @update:page="changeLogPage"
          @update:limit="changeLogLimit"
          :show-limit="false"
        />
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
import QePagination from "@/components/QePagination.vue";

import {
  LucideUserRound,
  LucideUserCircle,
  LucideBuilding2,
  LucideMail,
  LucidePhone,
  LucideNotebookPen,
  LucideMapPin,
  LucideMap,
  LucideWallet,
  LucideBookUser,
  LucideScanBarcode,  
  LucideBanknote,
  LucideFileText,
  LucideCalendar,
  LucideAlertCircle,
  LucideHistory,
  LucidePencilLine,
  LucideTrash2,
  LucideChevronDown
} from "lucide-vue-next";


const route = useRoute();
const router = useRouter();
const client = ref(null);
const estimates = ref([]);
const logs = ref([]);
const estimatesPagination = ref({ total: 0, limit: 20, offset: 0 });
const logsPagination = ref({ total: 0, limit: 10, offset: 0 });
const activeTab = ref("details");
const showConfirm = ref(false);
const store = useClientsStore();
const toast = useToast();
const showDetails = ref({})

onMounted(async () => {
  const { client: c, estimates: e, pagination: p } = await store.getClientWithEstimates(
    route.params.id,
    {
      limit: estimatesPagination.value.limit,
      offset: estimatesPagination.value.offset,
    }
  );
  client.value = c;
  estimates.value = e;
  estimatesPagination.value = p;

  const logsRes = await store.getClientLogs(route.params.id, {
    limit: logsPagination.value.limit,
    offset: logsPagination.value.offset,
  });
  logs.value = logsRes.items;
  logsPagination.value = logsRes.meta;
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

async function changeEstPage(p) {
  estimatesPagination.value.offset = (p - 1) * estimatesPagination.value.limit
  const { estimates: e, pagination: pinfo } = await store.getClientWithEstimates(route.params.id, {
    limit: estimatesPagination.value.limit,
    offset: estimatesPagination.value.offset,
  })
  estimates.value = e
  estimatesPagination.value = pinfo
}

async function changeEstLimit(l) {
  estimatesPagination.value.limit = l
  estimatesPagination.value.offset = 0
  await changeEstPage(1)
}

async function changeLogPage(p) {
  logsPagination.value.offset = (p - 1) * logsPagination.value.limit
  const res = await store.getClientLogs(route.params.id, {
    limit: logsPagination.value.limit,
    offset: logsPagination.value.offset,
  })
  logs.value = res.items
  logsPagination.value = res.meta
}

async function changeLogLimit(l) {
  logsPagination.value.limit = l
  logsPagination.value.offset = 0
  await changeLogPage(1)
}
</script>
