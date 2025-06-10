<template>
  <div class="py-8 max-w-6xl mx-auto">
    <!-- Ошибка -->
    <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
      {{ error }}
    </div>

    <div v-if="estimate" class="space-y-7">
      <!-- Заголовок и статус -->
      <div class="flex flex-wrap justify-between items-center pb-1 mb-7 gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <LucideFileText class="w-7 h-7 text-blue-600" />
            <span>Смета: {{ estimate.name }}</span>
            <span :class="[
              'inline-block align-middle rounded-full px-2 py-0.5 text-xs font-semibold ml-1',
              {
                'bg-gray-200 text-gray-800': estimate.status === 'draft',
                'bg-yellow-200 text-yellow-800': estimate.status === 'sent',
                'bg-green-200 text-green-800': estimate.status === 'approved',
                'bg-blue-200 text-blue-800': estimate.status === 'paid',
                'bg-red-200 text-red-800': estimate.status === 'cancelled',
              },
            ]">
              {{
              {
              draft: "Черновик",
              sent: "Отправлена",
              approved: "Согласована",
              paid: "Оплачена",
              cancelled: "Отменена",
              }[estimate.status]
              }}
            </span>
          </h1>
          <p v-if="isVersionView" class="mt-1 text-sm text-gray-500">
            Просмотр версии №{{ currentVersion }}
          </p>
        </div>

        <!-- Кнопки управления -->
        <div class="flex space-x-2 items-center relative">
          <!-- если мы в режиме версии, показываем другие кнопки -->
          <template v-if="isVersionView">
            <button @click="restoreVersion(currentVersion)" class="qe-btn-warning flex items-center">
              <RotateCcw class="w-4 h-4 mr-1" />
              <span>Восстановить</span>
            </button>
            <button @click="copyVersion(currentVersion)" class="qe-btn flex items-center">
              <ClipboardPaste class="w-4 h-4 mr-1" />
              <span>Копировать</span>
            </button>
            <button @click="deleteVersion(currentVersion)" class="qe-btn-danger flex items-center">
              <LucideTrash2 class="w-4 h-4 mr-1" />
              <span>Удалить версию</span>
            </button>
            <button @click="() => router.push({ path: `/estimates/${estimate.id}` })"
              class="qe-btn-secondary flex items-center">
              <Undo2 class="w-4 h-4 mr-1" />
              <span>Вернуться</span>
            </button>
          </template>
          <template v-else>
            <!-- Выпадающее меню -->
            <div class="relative" ref="menuRef">
              <button @click="showExport = !showExport" class="qe-btn-success inline-flex items-center">
                <Download class="w-4 h-4 mr-1" />
                <span>Экспортировать</span>
                <!-- <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg> -->
              </button>
              <div v-if="showExport"
                class="absolute right-0 mt-2 w-38 bg-white rounded-xl shadow-xl ring-1 ring-black/5 backdrop-blur-sm border border-gray-100 animate-fade-in z-50">
                <button @click="downloadJson(estimate.id)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-center text-sm text-gray-700 rounded-xl">
                  JSON
                </button>
                <button @click="downloadExcel(estimate)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-center text-gray-700 rounded-xl">
                  Excel
                </button>
                <button @click="downloadPdf(estimate)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-center text-gray-700 rounded-xl">
                  PDF
                </button>
              </div>
            </div>

            <!-- Основные кнопки -->
            <RouterLink :to="`/estimates/${estimate.id}/edit`" class="qe-btn-warning flex items-center">
              <LucidePencilLine class="w-4 h-4 mr-1" />
              <span>Редактировать</span>
            </RouterLink>
            <button @click="copyEstimate" class="qe-btn flex items-center">
              <ClipboardPaste class="w-4 h-4 mr-1" />
              <span>Копировать</span>
            </button>
            <button @click="confirmDelete" class="qe-btn-danger flex items-center">
              <LucideTrash2 class="w-4 h-4 mr-1" />
              <span>Удалить</span>
            </button>
          </template>
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

      <!-- Основной контент -->
      <div v-if="activeTab === 'details'">
        <!-- Краткая информация -->
        <div class="grid gap-4 text-sm text-gray-800 dark:text-gray-200 grid-cols-1 md:grid-cols-2">
          <div class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border dark:border-qe-black2 shadow-sm space-y-2">
            <div class="flex items-center gap-2 mt-2">
              <LucideUser class="w-5 h-5 text-blue-500" />
              <span><span class="font-semibold">Клиент: </span>
                <RouterLink :to="`/clients/${estimate.client.id}`" class="text-blue-700 hover:underline">
                  {{ estimate.client.name }}
                </RouterLink>
              </span>
            </div>
            <div v-if="estimate.event_datetime" class="flex items-center gap-2">
              <LucideCalendar class="w-5 h-5 text-yellow-500" />
              <span><span class="font-semibold">Дата и время: </span><span>{{
                  new Date(estimate.event_datetime).toLocaleString()
                  }}</span></span>
            </div>
            <div class="flex items-center gap-2">
              <LucideUserCircle class="w-5 h-5 text-green-500" />
              <span><span class="font-semibold">Ответственный: </span><span>{{ estimate.responsible }}</span></span>
            </div>
            <div v-if="estimate.event_place" class="flex items-center gap-2">
              <LucideMapPin class="w-5 h-5 text-pink-500" />
              <span><span class="font-semibold">Место: </span><span>{{ estimate.event_place }}</span></span>
            </div>
            <div class="flex items-center gap-2">
              <LucidePercentCircle class="w-5 h-5 text-indigo-500" />
              <span>
                <span class="font-semibold">НДС:</span>
                <span v-if="estimate.vat_enabled">
                  Включён ({{ estimate.vat_rate }}%)</span>
                <span v-else> Не включён</span>
              </span>
            </div>

            <div class="flex items-center gap-2">
              <LucideClock3 class="w-5 h-5 text-gray-400" />
              <span><span class="font-semibold">Создана:</span>
                {{ new Date(estimate.date).toLocaleString() }}</span>
            </div>
            <div class="flex items-center gap-2">
              <LucideRefreshCw class="w-5 h-5 text-gray-400" />
              <span><span class="font-semibold">Обновлена:</span>
                {{ new Date(estimate.updated_at).toLocaleString() }}</span>
            </div>
            <div class="flex items-center gap-2">
              <NotebookPen class="w-5 h-5 text-gray-400" />
              <span><span class="font-semibold">Примечания:</span>
                {{ estimate.notes || "—" }}</span>
            </div>
          </div>

          <!-- Общие суммы -->
          <div
            class="bg-white dark:bg-qe-black3 0 rounded-2xl shadow-sm p-6 border dark:border-qe-black2 flex flex-col gap-4 justify-center h-full">
            <div class="flex items-center gap-3">
              <LucideWallet class="w-7 h-7 text-blue-600" />
              <span class="text-lg font-bold">Суммы по смете</span>
            </div>
            <div class="space-y-2 mt-2">
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-2 text-gray-500">
                  <LucidePiggyBank class="w-5 h-5 text-green-600" />
                  <span>Внутренняя:</span>
                </div>
                <span class="text-lg font-semibold text-green-700 dark:text-green-400">{{ formatCurrency(totalInternal)
                  }}</span>
              </div>
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-2 text-gray-500">
                  <LucideReceipt class="w-5 h-5 text-blue-600" />
                  <span>Внешняя:</span>
                </div>
                <span class="text-lg font-semibold text-blue-700 dark:text-blue-400">{{ formatCurrency(totalExternal)
                  }}</span>
              </div>
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-2 text-gray-500">
                  <LucideArrowUpRight class="w-5 h-5 text-pink-600" />
                  <span>Разница:</span>
                </div>
                <span class="text-lg font-semibold text-pink-600 dark:text-pink-400">{{ formatCurrency(totalDiff)
                  }}</span>
              </div>
              <div v-if="estimate.vat_enabled" class="flex justify-between items-center">
                <div class="flex items-center gap-2 text-gray-500">
                  <LucidePercentCircle class="w-5 h-5 text-indigo-600" />
                  <span>НДС ({{ estimate.vat_rate }}%):</span>
                </div>
                <span class="text-lg font-semibold text-indigo-600 dark:text-indigo-400">{{ formatCurrency(vat)
                  }}</span>
              </div>
              <div v-if="estimate.vat_enabled"
                class="flex justify-between items-center border-t pt-2 mt-2 dark:border-qe-black2">
                <div class="flex items-center gap-2 text-gray-700 dark:text-white font-semibold">
                  <LucideCalculator class="w-5 h-5" />
                  <span>Итого с НДС:</span>
                </div>
                <span class="text-xl font-bold text-gray-800 dark:text-white">{{
                  formatCurrency(totalWithVat)
                  }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Категории и услуги -->
        <div class="mt-8">
          <div v-for="(groupItems, category) in groupedItems" :key="category"
            class="mb-6 border p-6 rounded-2xl bg-white dark:border-qe-black2 dark:bg-qe-black3 shadow">
            <div class="flex items-center justify-center gap-2 mb-3">
              <LucideFolder class="w-6 h-6 text-blue-500" />
              <h3 class="text-xl font-semibold text-gray-800 dark:text-white pb-1">
                {{ category }}
              </h3>
            </div>

            <div class="space-y-4">
              <div v-for="item in groupItems" :key="item.id"
                class="bg-white dark:bg-qe-black3 border border-gray-100 dark:border-qe-black2 rounded-xl shadow p-4 transition flex flex-col">
                <div class="flex flex-wrap justify-between items-center gap-2">
                  <div>
                    <div class="text-base font-semibold text-gray-900 dark:text-white flex items-center">
                      {{ item.name }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-300">
                      {{ item.description }}
                    </div>
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-300 whitespace-nowrap">
                    {{ item.quantity }} {{ item.unit }}
                  </div>
                </div>
                <div class="flex justify-between text-sm text-gray-600 dark:text-gray-300 mt-2">
                  <span>Внутр. цена за единицу:</span>
                  <span>{{ formatCurrency(item.internal_price) }}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>Внешн. цена за единицу:</span>
                  <span>{{ formatCurrency(item.external_price) }}</span>
                </div>
                <div class="flex justify-between font-semibold text-sm text-gray-900 dark:text-white">
                  <span>Итог (внутр.):</span>
                  <span>{{ formatCurrency(getItemInternal(item)) }}</span>
                </div>
                <div class="flex justify-between font-semibold text-sm text-gray-900 dark:text-white">
                  <span>Итог (внешн.):</span>
                  <span>{{ formatCurrency(getItemExternal(item)) }}</span>
                </div>
              </div>
            </div>
            <!-- Итоги по категории -->
            <div class="flex gap-3 justify-center mt-5">
              <div
                class="flex items-center gap-1 bg-gray-50 dark:bg-qe-black2 rounded-xl px-3 py-1 shadow border border-gray-100 dark:border-qe-black2">
                <LucidePiggyBank class="w-4 h-4 text-green-500" />
                <span class="text-xs text-gray-600 dark:text-gray-300">Итог по категории (внутр.):</span>
                <span class="font-semibold text-sm text-green-800 dark:text-green-300">{{
                  formatCurrency(getGroupInternal(groupItems)) }}</span>
              </div>
              <div
                class="flex items-center gap-1 bg-gray-50 dark:bg-qe-black2 rounded-xl px-3 py-1 shadow border border-gray-100 dark:border-qe-black2">
                <LucideReceipt class="w-4 h-4 text-blue-500" />
                <span class="text-xs text-gray-600 dark:text-gray-300">Итог по категории (внешн.):</span>
                <span class="font-semibold text-sm text-blue-800 dark:text-blue-300">{{
                  formatCurrency(getGroupExternal(groupItems)) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>


      <div v-else>

        <!-- История изменений -->
        <div v-if="logs.length" class="text-sm w-full mt-6">
          <h3 class="font-semibold mb-4">

            <span class="flex items-center gap-1">
              <LucideHistory class="w-5 h-5 text-blue-600" />
              <span>История изменений</span>
            </span>

          </h3>
          <div
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
                  {{ formatDate(log.timestamp) }}
                </div>
                <div class="flex-1 flex items-center gap-2 min-w-0">
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
                    {{ log.description }}
                  </span>
                  <span class="text-sm text-gray-500 truncate">— {{ log.user_name }}</span>
                </div>
                <!-- Важно: фиксированная ширина, text-right и truncate -->
                <div class="w-[140px] shrink-0 text-right pr-4">
                  <button v-if="log.details && log.details.length" @click="toggleDetails(log.id)"
                    class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded text-blue-600 hover:bg-blue-50 transition -mr-6">
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
                  class="mt-2 mb-2 pl-2 border-l dark:border-qe-black2 border-blue-200 text-sm space-y-1">
                  <li v-for="(d, i) in log.details" :key="i" class="text-blue-700 dark:text-blue-500">
                  <li v-if="typeof d === 'string'">
                    {{ d }}
                  </li>
                  <li v-else>
                    <span class="font-semibold">{{ d.label }}:</span>
                    <span class="mx-1 text-gray-500 line-through">
                      {{
                      isDate(d.old) && isDate(d.new)
                      ? formatDate(d.old)
                      : d.old
                      }}
                    </span>
                    <span class="-mx-1 -mr-2 text-blue-700 dark:text-blue-400 font-semibold">
                      →
                      {{
                      isDate(d.old) && isDate(d.new)
                      ? formatDate(d.new)
                      : d.new
                      }}
                    </span>
                  </li>
                  </li>
                </ul>
              </transition>
            </div>
          </div>
          <QePagination
            :total="logsPagination.total"
            :limit="logsPagination.limit"
            :offset="logsPagination.offset"
            @update:page="p => { logsPagination.offset = (p - 1) * logsPagination.limit; changeLogsPage(p); }"
            @update:limit="l => { logsPagination.limit = l; logsPagination.offset = 0; changeLogsLimit(l); }"
            :show-limit="false"
          />
        </div>

        <div v-if="versions.length" class="mt-2 pt-6 text-sm">
          <h3 class="font-semibold mb-4">
            <span class="flex items-center gap-1">
              <GitGraph class="w-5 h-5 text-blue-600" />
              <span>История версий</span>
            </span>

          </h3>
          <div
            class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black3">
            <table class="w-full text-sm qe-table">
              <thead>
                <tr class="bg-gray-50 dark:bg-qe-black2">
                  <th class="qe-table-th text-left">Версия</th>
                  <th class="qe-table-th text-left">Дата создания</th>
                  <th class="qe-table-th text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in versions" :key="v.version"
                  class="hover:bg-gray-100 dark:hover:bg-gray-800 border-b last:border-b-0 transition dark:bg-qe-black3">
                  <td class="qe-table-td">№{{ v.version }}</td>
                  <td class="qe-table-td">
                    {{ new Date(v.created_at).toLocaleString() }}
                  </td>
                  <td class="qe-table-td text-right space-x-2">
                    <button @click="viewVersion(v.version)"
                      class="py-1 px-2 rounded-lg bg-blue-600 font-medium text-sm text-white transition border border-transparent shadow-sm hover:bg-blue-700 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 active:scale-95 transition">
                      Просмотр
                    </button>
                    <button @click="deleteVersion(v.version)"
                      class="py-1 px-2 rounded-lg bg-red-600 font-medium text-sm text-white transition border border-transparent shadow-sm hover:bg-red-700 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 active:scale-95 transition">
                      Удалить
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <QePagination
            :total="versionsPagination.total"
            :limit="versionsPagination.limit"
            :offset="versionsPagination.offset"
            @update:page="p => { versionsPagination.offset = (p - 1) * versionsPagination.limit; changeVersPage(p); }"
            @update:limit="l => { versionsPagination.limit = l; versionsPagination.offset = 0; changeVersLimit(l); }"
            :show-limit="false"
          />
        </div>
      </div>
    </div>
    <!-- Модалка -->
    <QeModal v-model="showConfirm" @confirm="deleteEstimate">
      Вы уверены, что хотите удалить данную смету?
      <template #confirm>Удалить</template>
      <template #cancel>Отмена</template>
    </QeModal>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useEstimatesStore } from "@/store/estimates";
import { onClickOutside } from "@vueuse/core";
import { useToast } from "vue-toastification";
import QeModal from "@/components/QeModal.vue";
import QePagination from "@/components/QePagination.vue";
import fileDownload from "js-file-download";

import {
  LucideFileText,
  LucideUser,
  Undo2,
  RotateCcw,
  LucideCalendar,
  LucideUserCircle,
  LucideMapPin,
  LucidePercentCircle,
  LucidePencilLine,
  ClipboardPaste,
  LucideTrash2,
  Download,
  LucideClock3,
  LucideRefreshCw,
  LucideWallet,
  LucideHistory,
  LucidePiggyBank,
  LucideReceipt,
  GitGraph,
  LucideArrowUpRight,
  LucideCalculator,
  LucideFolder,
  NotebookPen,
} from "lucide-vue-next";



const route = useRoute();
const router = useRouter();
const store = useEstimatesStore();
const toast = useToast();

const versionParam = computed(() =>
  route.query.version ? Number(route.query.version) : null,
);
const isVersionView = computed(() => versionParam.value !== null);
const currentVersion = ref(null);

const showExport = ref(false);
const menuRef = ref(null);
const showConfirm = ref(false);

const estimate = ref(null);
const logs = ref([]);
const versions = ref([]);
const logsPagination = ref({ total: 0, limit: 10, offset: 0 });
const versionsPagination = ref({ total: 0, limit: 10, offset: 0 });
const error = ref(null);

const activeTab = ref("details");

const showDetails = ref({})

function toggleDetails(id) {
  showDetails.value[id] = !showDetails.value[id]
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

async function loadAll() {
  const id = route.params.id;
  try {
    if (versionParam.value) {
      const ver = await store.getEstimateVersion(versionParam.value, id);
      currentVersion.value = versionParam.value;
      estimate.value = ver.payload;
      activeTab.value = "details";
    } else {
      estimate.value = await store.getEstimateById(id);
    }

    const logsRes = await store.getEstimateLogs(id, {
      limit: logsPagination.value.limit,
      offset: logsPagination.value.offset,
    });
    logs.value = logsRes.items;
    logsPagination.value = logsRes.meta;

    const versRes = await store.getEstimateVersions(id, {
      limit: versionsPagination.value.limit,
      offset: versionsPagination.value.offset,
    });
    versions.value = versRes.items;
    versionsPagination.value = versRes.meta;
    error.value = null;
  } catch (e) {
    if (e.response?.status === 404) error.value = "❌ Смета не найдена.";
    else if (e.response?.status === 403) error.value = "🚫 Нет доступа.";
    else error.value = "⚠️ Ошибка загрузки.";
  }
}

function isDate(val) {
  // Проверяет, является ли значение датой или строкой-датой
  if (!val) return false;
  if (val instanceof Date) return true;
  // Проверка на строку в формате ISO или похожем на дату
  return (
    typeof val === "string" &&
    !isNaN(Date.parse(val))
  );
}

onMounted(loadAll);
watch(() => route.query.version, loadAll);

onUnmounted(() => {
  store.currentEstimate = null;
});

onClickOutside(menuRef, () => {
  showExport.value = false;
});

function confirmDelete() {
  showConfirm.value = true;
}

async function copyEstimate() {
  const original = await store.getEstimateById(estimate.value.id);
  store.setCopiedEstimate(original);
  router.push("/estimates/create");
}

async function deleteEstimate() {
  await store.deleteEstimate(route.params.id);
  toast.success("Смета удалена");
  router.push("/estimates");
}

const groupedItems = computed(() => {
  const groups = {};
  for (const item of estimate.value?.items || []) {
    const category = item.category?.trim() || "Без категории";
    if (!groups[category]) groups[category] = [];
    groups[category].push(item);
  }
  return groups;
});

function getGroupInternal(group) {
  return group.reduce((sum, item) => sum + getItemInternal(item), 0);
}
function getGroupExternal(group) {
  return group.reduce((sum, item) => sum + getItemExternal(item), 0);
}

function getItemInternal(item) {
  return item.quantity * item.internal_price;
}

function getItemExternal(item) {
  return item.quantity * item.external_price;
}

const totalInternal = computed(
  () =>
    estimate.value?.items?.reduce(
      (sum, item) => sum + getItemInternal(item),
      0,
    ) || 0,
);
const totalExternal = computed(
  () =>
    estimate.value?.items?.reduce(
      (sum, item) => sum + getItemExternal(item),
      0,
    ) || 0,
);

const totalDiff = computed(() => totalExternal.value - totalInternal.value);

const vat = computed(() =>
  estimate.value?.vat_enabled
    ? totalExternal.value * (estimate.value.vat_rate / 100)
    : 0,
);
const totalWithVat = computed(() => totalExternal.value + vat.value);

function formatCurrency(val) {
  return `${val.toFixed(2)} ₽`;
}

async function downloadJson(id) {
  await store.exportEstimate(id);
}


async function downloadExcel(estimate) {
  try {
    const blob = await store.downloadEstimateExcel(estimate.id);
    fileDownload(blob, `${estimate.name}.xlsx`);
    toast.success("Excel успешно загружен");
  } catch (e) {
    console.error(e);
    toast.error("Ошибка при загрузке Excel");
  }
}

async function downloadPdf(estimate) {
  try {
    const blob = await store.downloadEstimatePdf(estimate.id);
    fileDownload(blob, `${estimate.name}.pdf`);
    toast.success("PDF успешно загружен");
  } catch (e) {
    console.error(e);
    toast.error("Ошибка при загрузке PDF");
  }
}

async function viewVersion(ver) {
  const id = route.params.id;
  // 1. Навигация
  await router.push({ path: `/estimates/${id}`, query: { version: ver } });
  // 2. Перезагрузить данные (чтобы loadAll учёл новый query.version)
  await loadAll();
  setTimeout(() => {
    const layoutMain = document.querySelector("main.overflow-y-auto");
    if (layoutMain) {
      layoutMain.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, 50);
}

async function restoreVersion(version) {
  const id = route.params.id;
  try {
    await store.restoreVersion(version, estimate.value.id);
    toast.success(`Версия №${version} восстановлена`);
    await router.push({ path: `/estimates/${id}` });
    await loadAll();
  } catch (err) {
    console.error(err);
    toast.error("Не удалось восстановить версию");
  }
}

async function deleteVersion(version) {
  if (!confirm(`Вы точно хотите удалить версию №${version}?`)) return;

  try {
    await store.deleteVersion(version, estimate.value.id);
    toast.success(`Версия №${version} удалена`);
    await router.push({ path: `/estimates/${estimate.value.id}` });
    await loadAll();
  } catch (err) {
    console.error(err);
    toast.error("Не удалось удалить версию");
  }
}

async function changeLogsPage(p) {
  logsPagination.value.offset = (p - 1) * logsPagination.value.limit
  await loadAll()
}

async function changeLogsLimit(l) {
  logsPagination.value.limit = l
  logsPagination.value.offset = 0
  await loadAll()
}

async function changeVersPage(p) {
  versionsPagination.value.offset = (p - 1) * versionsPagination.value.limit
  await loadAll()
}

async function changeVersLimit(l) {
  versionsPagination.value.limit = l
  versionsPagination.value.offset = 0
  await loadAll()
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>