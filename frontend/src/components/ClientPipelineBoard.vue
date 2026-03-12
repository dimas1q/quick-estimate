<script setup>
import { computed } from "vue";

const props = defineProps({
  pipeline: {
    type: Object,
    default: () => ({
      summary: {
        lead_count: 0,
        quote_count: 0,
        approved_count: 0,
        paid_count: 0,
        total_expected_revenue: 0,
        weighted_forecast: 0,
      },
      items: [],
    }),
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const STAGES = [
  {
    key: "lead",
    label: "Лид",
    chipClass:
      "bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-200",
    columnClass: "border-slate-200 dark:border-slate-800",
  },
  {
    key: "quote",
    label: "КП",
    chipClass:
      "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-200",
    columnClass: "border-sky-200 dark:border-sky-900/40",
  },
  {
    key: "approved",
    label: "Согласовано",
    chipClass:
      "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-200",
    columnClass: "border-amber-200 dark:border-amber-900/40",
  },
  {
    key: "paid",
    label: "Оплачено",
    chipClass:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200",
    columnClass: "border-emerald-200 dark:border-emerald-900/40",
  },
];

const groupedItems = computed(() => {
  const groups = {
    lead: [],
    quote: [],
    approved: [],
    paid: [],
  };

  for (const item of props.pipeline?.items || []) {
    const stage = item.pipeline_stage;
    if (groups[stage]) {
      groups[stage].push(item);
    }
  }

  return groups;
});

function getStageCount(stageKey) {
  const summary = props.pipeline?.summary || {};
  if (stageKey === "lead") return Number(summary.lead_count || 0);
  if (stageKey === "quote") return Number(summary.quote_count || 0);
  if (stageKey === "approved") return Number(summary.approved_count || 0);
  return Number(summary.paid_count || 0);
}

function formatCurrency(value) {
  return `${Number(value || 0).toFixed(2)} ₽`;
}

function formatDate(dateString) {
  if (!dateString) return "—";
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("ru-RU");
}
</script>

<template>
  <div class="space-y-5">
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">Лиды</p>
        <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{{ pipeline.summary.lead_count || 0 }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">КП</p>
        <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{{ pipeline.summary.quote_count || 0 }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">Согласовано</p>
        <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{{ pipeline.summary.approved_count || 0 }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">Оплачено</p>
        <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{{ pipeline.summary.paid_count || 0 }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">Общая ожидаемая выручка</p>
        <p class="mt-1 text-xl font-bold text-gray-900 dark:text-white">{{ formatCurrency(pipeline.summary.total_expected_revenue) }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-4 dark:border-qe-black2 dark:bg-qe-black3">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-300">Взвешенный прогноз</p>
        <p class="mt-1 text-xl font-bold text-gray-900 dark:text-white">{{ formatCurrency(pipeline.summary.weighted_forecast) }}</p>
      </div>
    </div>

    <div v-if="loading" class="grid grid-cols-1 gap-4 xl:grid-cols-4">
      <div v-for="n in 4" :key="n" class="h-48 animate-pulse rounded-2xl border border-gray-200 bg-white dark:border-qe-black2 dark:bg-qe-black3" />
    </div>

    <div v-else class="grid grid-cols-1 gap-4 xl:grid-cols-4">
      <div
        v-for="stage in STAGES"
        :key="stage.key"
        class="rounded-2xl border bg-white p-3 dark:bg-qe-black3"
        :class="stage.columnClass"
      >
        <div class="mb-3 flex items-center justify-between">
          <span class="rounded-full px-2 py-1 text-xs font-semibold" :class="stage.chipClass">{{ stage.label }}</span>
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-300">{{ getStageCount(stage.key) }}</span>
        </div>

        <div class="space-y-3">
          <RouterLink
            v-for="client in groupedItems[stage.key]"
            :key="client.id"
            :to="`/clients/${client.id}`"
            class="block rounded-xl border border-gray-200 bg-white p-3 transition hover:shadow-md dark:border-qe-black2 dark:bg-qe-black2"
          >
            <p class="truncate text-sm font-semibold text-gray-900 dark:text-white">{{ client.name }}</p>
            <p class="truncate text-xs text-gray-500 dark:text-gray-300">{{ client.company || "—" }}</p>
            <div class="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-300">
              <p>Ожидаемо: {{ formatCurrency(client.pipeline_expected_revenue) }}</p>
              <p>Прогноз: {{ formatCurrency(client.forecast_amount) }}</p>
              <p>Оплачено: {{ formatCurrency(client.paid_revenue) }}</p>
              <p>Последняя смета: {{ formatDate(client.last_estimate_date) }}</p>
            </div>
          </RouterLink>

          <div
            v-if="!groupedItems[stage.key].length"
            class="rounded-xl border border-dashed border-gray-200 px-3 py-6 text-center text-xs text-gray-400 dark:border-qe-black2 dark:text-gray-500"
          >
            Нет клиентов
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
