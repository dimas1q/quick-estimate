## frontend/src/pages/client/ClientDetailsPage.vue
<template>
  <div class="py-8 max-w-6xl mx-auto">
    <div
      v-if="!client"
      class="text-center py-10 text-lg text-gray-500 dark:text-gray-400"
    >
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

      <div
        class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 mb-6 w-fit"
      >
        <button
          :class="[
            'px-5 py-2 rounded-lg text-sm font-semibold transition',
            activeTab === 'details'
              ? 'bg-white dark:bg-gray-900 text-blue-600 shadow'
              : 'text-gray-500 hover:text-blue-600',
          ]"
          @click="activeTab = 'details'"
        >
          Сведения
        </button>
        <button
          :class="[
            'px-5 py-2 rounded-lg text-sm font-semibold transition',
            activeTab === 'history'
              ? 'bg-white dark:bg-gray-900 text-blue-600 shadow'
              : 'text-gray-500 hover:text-blue-600',
          ]"
          @click="activeTab = 'history'"
        >
          История
        </button>
      </div>

      <div
        class="grid gap-3 text-sm text-gray-800 dark:text-gray-200"
        v-if="activeTab === 'details'"
      >
        <div
          class="grid grid-cols-2 gap-4 shadow-sm border dark:border-qe-black2 bg-white dark:bg-qe-black3 rounded-2xl p-6"
        >
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
      <div
        class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-sm p-6 mt-6"
        v-if="activeTab === 'details'"
      >
        <h2 class="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
          Сметы клиента
        </h2>
        <div
          v-if="estimates.length > 0"
          class="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div
            v-for="e in estimates"
            :key="e.id"
            class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 p-4 rounded-xl shadow-sm flex flex-col gap-2 hover:shadow-md transition"
          >
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
        <div
          v-else
          class="text-center text-gray-500 border border-gray-200 dark:border-qe-black2 p-4 rounded-xl py-8 mt-2 bg-white dark:bg-qe-black3"
        >
          Сметы отсутствуют.
        </div>
      </div>

      <div
        v-if="activeTab === 'history'"
        class="border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-sm p-6"
      >
        <h2 class="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
          История
        </h2>
        <div
          v-if="logs.length"
          class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700"
        >
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-qe-black">
                <th class="qe-table-th text-left">Дата</th>
                <th class="qe-table-th text-left">Событие</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="l in logs"
                :key="l.id"
                class="hover:bg-gray-100 dark:hover:bg-gray-800 transition"
              >
                <td class="qe-table-td">
                  {{ new Date(l.timestamp).toLocaleString() }}
                </td>
                <td class="qe-table-td">{{ l.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-gray-500 text-sm">История пуста.</div>

        <div class="mt-4 flex gap-2">
          <input
            v-model="newComment"
            type="text"
            placeholder="Комментарий"
            class="qe-input flex-grow"
          />
          <button @click="submitComment" class="qe-btn-primary">
            Добавить
          </button>
        </div>
      </div>
    </div>

    <!-- Модалка подтверждения удаления -->
    <QeModal v-model="showConfirm" @confirm="deleteClient">
      Вы уверены, что хотите удалить данного клиента?
      <template #confirm>Да, удалить</template>
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
const newComment = ref("");
const activeTab = ref("details");
const showConfirm = ref(false);
const store = useClientsStore();
const toast = useToast();

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

async function submitComment() {
  if (!newComment.value.trim()) return;
  const log = await store.addClientLog(route.params.id, {
    action: "Комментарий",
    description: newComment.value,
  });
  logs.value.push(log);
  newComment.value = "";
}
</script>
