<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  leftVersion: {
    type: Object,
    default: null,
  },
  rightVersion: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update:modelValue"]);

const STATUS_LABELS = {
  draft: "Черновик",
  sent: "Отправлена",
  approved: "Согласована",
  paid: "Оплачена",
  cancelled: "Отменена",
};

const leftPayload = computed(() => props.leftVersion?.payload || {});
const rightPayload = computed(() => props.rightVersion?.payload || {});

const leftVersionLabel = computed(() =>
  props.leftVersion?.version ? `Версия №${props.leftVersion.version}` : "Версия A"
);
const rightVersionLabel = computed(() =>
  props.rightVersion?.version ? `Версия №${props.rightVersion.version}` : "Версия B"
);

function closeModal() {
  emit("update:modelValue", false);
}

function toNumber(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

function normalizeScalar(value) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function normalizeDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return normalizeScalar(value);
  return date.toLocaleString("ru-RU");
}

function normalizeStatus(value) {
  if (!value) return "—";
  return STATUS_LABELS[value] || value;
}

function normalizeClient(value) {
  if (!value) return "—";
  return value.company || value.name || "—";
}

function normalizeYesNo(value) {
  return value ? "Да" : "Нет";
}

function normalizeMoney(value) {
  return `${toNumber(value).toFixed(2)} ₽`;
}

function getItems(payload) {
  return Array.isArray(payload?.items) ? payload.items : [];
}

function calcTotals(payload) {
  const items = getItems(payload);
  const totalInternal = payload?.use_internal_price
    ? items.reduce(
        (sum, item) => sum + toNumber(item.quantity) * toNumber(item.internal_price),
        0,
      )
    : 0;
  const totalExternal = items.reduce(
    (sum, item) => sum + toNumber(item.quantity) * toNumber(item.external_price),
    0,
  );
  const vat = payload?.vat_enabled
    ? totalExternal * (toNumber(payload.vat_rate) / 100)
    : 0;
  return {
    totalInternal,
    totalExternal,
    totalDiff: totalExternal - totalInternal,
    vat,
    totalWithVat: totalExternal + vat,
  };
}

function valuesDiffer(leftValue, rightValue) {
  return leftValue !== rightValue;
}

const fieldRows = computed(() => {
  const left = leftPayload.value;
  const right = rightPayload.value;
  const leftTotals = calcTotals(left);
  const rightTotals = calcTotals(right);

  return [
    {
      label: "Название",
      left: normalizeScalar(left.name),
      right: normalizeScalar(right.name),
    },
    {
      label: "Клиент",
      left: normalizeClient(left.client),
      right: normalizeClient(right.client),
    },
    {
      label: "Ответственный",
      left: normalizeScalar(left.responsible),
      right: normalizeScalar(right.responsible),
    },
    {
      label: "Статус",
      left: normalizeStatus(left.status),
      right: normalizeStatus(right.status),
    },
    {
      label: "Дата мероприятия",
      left: normalizeDate(left.event_datetime),
      right: normalizeDate(right.event_datetime),
    },
    {
      label: "Место проведения",
      left: normalizeScalar(left.event_place),
      right: normalizeScalar(right.event_place),
    },
    {
      label: "НДС включен",
      left: normalizeYesNo(Boolean(left.vat_enabled)),
      right: normalizeYesNo(Boolean(right.vat_enabled)),
    },
    {
      label: "Ставка НДС",
      left: `${toNumber(left.vat_rate)}%`,
      right: `${toNumber(right.vat_rate)}%`,
    },
    {
      label: "Внутренняя цена",
      left: normalizeYesNo(Boolean(left.use_internal_price)),
      right: normalizeYesNo(Boolean(right.use_internal_price)),
    },
    {
      label: "Количество услуг",
      left: String(getItems(left).length),
      right: String(getItems(right).length),
    },
    {
      label: "Продажная сумма",
      left: normalizeMoney(leftTotals.totalExternal),
      right: normalizeMoney(rightTotals.totalExternal),
    },
    {
      label: "Себестоимость",
      left: normalizeMoney(leftTotals.totalInternal),
      right: normalizeMoney(rightTotals.totalInternal),
    },
    {
      label: "Маржа",
      left: normalizeMoney(leftTotals.totalDiff),
      right: normalizeMoney(rightTotals.totalDiff),
    },
    {
      label: "НДС сумма",
      left: normalizeMoney(leftTotals.vat),
      right: normalizeMoney(rightTotals.vat),
    },
    {
      label: "Итого с НДС",
      left: normalizeMoney(leftTotals.totalWithVat),
      right: normalizeMoney(rightTotals.totalWithVat),
    },
  ].map((row) => ({
    ...row,
    changed: valuesDiffer(row.left, row.right),
  }));
});

function formatItemCell(item) {
  if (!item) return "—";
  return [
    item.name || "Без названия",
    `Категория: ${item.category || "—"}`,
    `Кол-во: ${toNumber(item.quantity)} ${item.unit || "шт"}`,
    `Внутр.: ${normalizeMoney(item.internal_price)}`,
    `Внешн.: ${normalizeMoney(item.external_price)}`,
  ];
}

function itemsEqual(leftItem, rightItem) {
  if (!leftItem && !rightItem) return true;
  if (!leftItem || !rightItem) return false;
  return (
    normalizeScalar(leftItem.name) === normalizeScalar(rightItem.name) &&
    normalizeScalar(leftItem.category) === normalizeScalar(rightItem.category) &&
    toNumber(leftItem.quantity) === toNumber(rightItem.quantity) &&
    normalizeScalar(leftItem.unit) === normalizeScalar(rightItem.unit) &&
    toNumber(leftItem.internal_price) === toNumber(rightItem.internal_price) &&
    toNumber(leftItem.external_price) === toNumber(rightItem.external_price)
  );
}

const itemRows = computed(() => {
  const leftItems = getItems(leftPayload.value);
  const rightItems = getItems(rightPayload.value);
  const maxRows = Math.max(leftItems.length, rightItems.length);

  return Array.from({ length: maxRows }, (_, index) => {
    const leftItem = leftItems[index] || null;
    const rightItem = rightItems[index] || null;

    return {
      index: index + 1,
      leftItem,
      rightItem,
      leftLines: formatItemCell(leftItem),
      rightLines: formatItemCell(rightItem),
      changed: !itemsEqual(leftItem, rightItem),
    };
  });
});

const changedFieldCount = computed(
  () => fieldRows.value.filter((row) => row.changed).length,
);
const changedItemCount = computed(
  () => itemRows.value.filter((row) => row.changed).length,
);
const hasItemRows = computed(() => itemRows.value.length > 0);

const leftVersionDate = computed(() => normalizeDate(props.leftVersion?.created_at));
const rightVersionDate = computed(() => normalizeDate(props.rightVersion?.created_at));
</script>

<template>
  <transition name="modal-fade">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[70] flex items-start justify-center overflow-y-auto px-4 py-8"
    >
      <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" @click="closeModal" />

      <div
        class="relative z-10 w-full max-w-6xl rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-black/10 dark:bg-qe-black2 dark:ring-white/10"
      >
        <div class="flex flex-wrap items-start justify-between gap-3 border-b border-gray-200 pb-4 dark:border-qe-black3">
          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Сравнение версий сметы</h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-300">
              Изменено полей: {{ changedFieldCount }}. Изменено строк услуг: {{ changedItemCount }}.
            </p>
          </div>
          <button
            class="rounded-lg border border-gray-200 px-3 py-1 text-sm font-medium text-gray-600 transition hover:bg-gray-100 dark:border-qe-black3 dark:text-gray-200 dark:hover:bg-qe-black3"
            @click="closeModal"
          >
            Закрыть
          </button>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="rounded-xl border border-blue-100 bg-blue-50/60 p-3 dark:border-blue-900/40 dark:bg-blue-950/20">
            <p class="text-sm font-semibold text-blue-700 dark:text-blue-300">{{ leftVersionLabel }}</p>
            <p class="text-xs text-blue-600/80 dark:text-blue-200/80">{{ leftVersionDate }}</p>
          </div>
          <div class="rounded-xl border border-indigo-100 bg-indigo-50/60 p-3 dark:border-indigo-900/40 dark:bg-indigo-950/20">
            <p class="text-sm font-semibold text-indigo-700 dark:text-indigo-300">{{ rightVersionLabel }}</p>
            <p class="text-xs text-indigo-600/80 dark:text-indigo-200/80">{{ rightVersionDate }}</p>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto rounded-xl border border-gray-200 dark:border-qe-black3">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 dark:bg-qe-black3">
              <tr>
                <th class="px-3 py-2 text-left font-semibold text-gray-700 dark:text-gray-200">Поле</th>
                <th class="px-3 py-2 text-left font-semibold text-blue-700 dark:text-blue-300">{{ leftVersionLabel }}</th>
                <th class="px-3 py-2 text-left font-semibold text-indigo-700 dark:text-indigo-300">{{ rightVersionLabel }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-qe-black3">
              <tr
                v-for="row in fieldRows"
                :key="row.label"
                :class="row.changed ? 'bg-amber-50/70 dark:bg-amber-900/20' : 'bg-white dark:bg-qe-black2'"
              >
                <td class="px-3 py-2 font-medium text-gray-700 dark:text-gray-200">{{ row.label }}</td>
                <td class="px-3 py-2" :class="row.changed ? 'text-blue-800 dark:text-blue-200' : 'text-gray-600 dark:text-gray-300'">
                  {{ row.left }}
                </td>
                <td class="px-3 py-2" :class="row.changed ? 'text-indigo-800 dark:text-indigo-200' : 'text-gray-600 dark:text-gray-300'">
                  {{ row.right }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-5 overflow-x-auto rounded-xl border border-gray-200 dark:border-qe-black3">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 dark:bg-qe-black3">
              <tr>
                <th class="px-3 py-2 text-left font-semibold text-gray-700 dark:text-gray-200" style="width: 60px">#</th>
                <th class="px-3 py-2 text-left font-semibold text-blue-700 dark:text-blue-300">{{ leftVersionLabel }}</th>
                <th class="px-3 py-2 text-left font-semibold text-indigo-700 dark:text-indigo-300">{{ rightVersionLabel }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-qe-black3">
              <tr v-if="!hasItemRows" class="bg-white dark:bg-qe-black2">
                <td colspan="3" class="px-3 py-4 text-center text-gray-500 dark:text-gray-300">
                  В выбранных версиях нет услуг для сравнения
                </td>
              </tr>
              <tr
                v-for="row in itemRows"
                :key="row.index"
                :class="row.changed ? 'bg-rose-50/70 dark:bg-rose-900/20' : 'bg-white dark:bg-qe-black2'"
              >
                <td class="px-3 py-2 font-medium text-gray-700 dark:text-gray-200 align-top">{{ row.index }}</td>
                <td class="px-3 py-2 align-top">
                  <div
                    v-for="line in row.leftLines"
                    :key="`left-${row.index}-${line}`"
                    class="leading-5 text-gray-700 dark:text-gray-300"
                  >
                    {{ line }}
                  </div>
                </td>
                <td class="px-3 py-2 align-top">
                  <div
                    v-for="line in row.rightLines"
                    :key="`right-${row.index}-${line}`"
                    class="leading-5 text-gray-700 dark:text-gray-300"
                  >
                    {{ line }}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
