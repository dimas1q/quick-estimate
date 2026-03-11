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
              'inline-block align-middle rounded-full px-2 py-0.5 text-xs font-semibold ml-1 mt-1',
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
            <span v-if="estimate.read_only"
              class="inline-block align-middle rounded-full px-2 py-0.5 text-xs font-semibold ml-1 mt-1 bg-amber-100 text-amber-800">
              Только чтение
            </span>
          </h1>
          <p v-if="isVersionView" class="mt-1 text-sm text-gray-500">
            Просмотр версии №{{ currentVersion }}
          </p>
        </div>

        <!-- Кнопки управления -->

      </div>

      <div class="flex items-center justify-between mb-6 gap-4">
        <!-- Табы -->
        <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 w-fit">
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

        <div class="flex flex-wrap justify-end gap-2 items-center relative">
          <!-- если мы в режиме версии, показываем другие кнопки -->
          <template v-if="isVersionView">
            <button v-if="!estimate.read_only" @click="restoreVersion(currentVersion)" class="qe-btn-warning flex items-center">
              <RotateCcw class="w-4 h-4 mr-1" />
              <span>Восстановить</span>
            </button>
            <button @click="copyVersion(currentVersion)" class="qe-btn flex items-center">
              <ClipboardPaste class="w-4 h-4 mr-1" />
              <span>Копировать</span>
            </button>
            <button v-if="!estimate.read_only" @click="deleteVersion(currentVersion)" class="qe-btn-danger flex items-center">
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
              <button @click="showExport = !showExport; showActionsMenu = false"
                class="qe-btn-success inline-flex items-center gap-1 px-5 py-2">
                <Download class="w-4 h-4 mr-1" />
                <span>Экспортировать</span>
                <svg class="w-4 h-4 ml-2 transition-transform duration-200" :class="{ 'rotate-180': showExport }"
                  fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-if="showExport"
                class="absolute right-0 mt-2 w-max min-w-0 bg-white rounded-xl shadow-xl ring-1 ring-black/5 backdrop-blur-sm border border-gray-100 animate-fade-in z-50">
                <button @click="downloadJson(estimate.id)"
                  class="block whitespace-nowrap text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700 rounded-t-xl">
                  JSON
                </button>
                <button @click="downloadExcel(estimate)"
                  class="block whitespace-nowrap text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700">
                  Excel
                </button>
                <button @click="downloadPdf(estimate)"
                  class="block whitespace-nowrap text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700 rounded-b-xl">
                  PDF
                </button>
              </div>
            </div>
            <div class="relative" ref="actionsMenuRef">
              <button @click="showActionsMenu = !showActionsMenu; showExport = false"
                class="qe-btn-secondary inline-flex items-center gap-1 px-5 py-2">
                <MoreHorizontal class="w-4 h-4 mr-1" />
                <span>Действия</span>
                <svg class="w-4 h-4 ml-2 transition-transform duration-200" :class="{ 'rotate-180': showActionsMenu }"
                  fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-if="showActionsMenu"
                class="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl ring-1 ring-black/5 backdrop-blur-sm border border-gray-100 animate-fade-in z-50">
                <button @click="onActionMenuClick(openSendModal)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700 rounded-t-xl">
                  Отправить email
                </button>
                <button @click="onActionMenuClick(copyEstimate)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700">
                  Копировать смету
                </button>
                <button @click="onActionMenuClick(toggleReadOnly)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700"
                  :class="{ 'rounded-b-xl': estimate.read_only }">
                  {{ estimate.read_only ? 'Снять режим только чтение' : 'Перевести в только чтение' }}
                </button>
                <button v-if="!estimate.read_only" @click="onActionMenuClick(goToEdit)"
                  class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700">
                  Редактировать
                </button>
                <button v-if="!estimate.read_only" @click="onActionMenuClick(confirmDelete)"
                  class="block w-full text-left px-4 py-2 hover:bg-red-50 transition-colors text-sm text-red-600 rounded-b-xl">
                  Удалить
                </button>
              </div>
            </div>
          </template>
        </div>

      </div>

      <!-- Основной контент -->
      <div v-if="activeTab === 'details'">
        <!-- Краткая информация -->
        <div class="grid gap-4 text-sm text-gray-800 dark:text-gray-200 grid-cols-1 md:grid-cols-2">
          <!-- Левый блок: Краткая информация -->
          <div
            class="bg-white dark:bg-qe-black3 rounded-2xl p-6 border dark:border-qe-black2 shadow-sm space-y-2 h-full flex flex-col">
            <!-- Заголовок всегда сверху -->
            <div class="flex items-center gap-2 mb-2">
              <Info class="w-6 h-6 text-blue-600" />
              <span class="text-lg font-bold">Основная информация</span>
            </div>
            <!-- Данные по центру блока -->
            <div class="flex-1 flex flex-col justify-center space-y-2">
              <div v-if="estimate.client" class="flex items-center gap-2">
                <LucideUser class="w-5 h-5 text-blue-500" />
                <span><span class="font-semibold">Клиент: </span>
                  <RouterLink :to="`/clients/${estimate.client.id}`" class="text-blue-700 hover:underline">
                    {{ estimate.client.name }}
                  </RouterLink>
                </span>
              </div>
              <div class="flex items-center gap-2">
                <LucideUserCircle class="w-5 h-5 text-green-500" />
                <span><span class="font-semibold">Ответственный: </span><span>{{ estimate.responsible }}</span></span>
              </div>
              <div v-if="estimate.event_datetime" class="flex items-center gap-2">
                <LucideCalendar class="w-5 h-5 text-yellow-500" />
                <span><span class="font-semibold">Дата и время: </span><span>{{
                  new Date(estimate.event_datetime).toLocaleString()
                }}</span></span>
              </div>
              <div v-if="estimate.event_place" class="flex items-center gap-2">
                <LucideMapPin class="w-5 h-5 text-pink-500" />
                <span><span class="font-semibold">Место проведения: </span><span>{{ estimate.event_place
                }}</span></span>
              </div>
              <div class="flex items-center gap-2">
                <LucidePercentCircle class="w-5 h-5 text-indigo-500" />
                <span>
                  <span class="font-semibold">НДС:</span>
                  <span v-if="estimate.vat_enabled">
                    Включён ({{ estimate.vat_rate }}%)</span>
                  <span v-else> Выключен</span>
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
            </div>
          </div>

          <!-- Общие суммы -->
          <div
            class="bg-white dark:bg-qe-black3 rounded-2xl shadow-sm p-6 border dark:border-qe-black2 flex flex-col h-full">
            <!-- Заголовок всегда сверху -->
            <div class="flex items-center gap-2 mb-2">
              <LucideWallet class="w-6 h-6 text-blue-600" />
              <span class="text-lg font-bold">Суммы по смете</span>
            </div>
            <!-- Все остальное по центру блока -->
            <div class="flex-1 flex flex-col justify-center">
              <div class="space-y-2 mt-2">
                <div v-if="estimate.use_internal_price" class="flex justify-between items-center">
                  <div class="flex items-center gap-2 text-gray-500">
                    <LucidePiggyBank class="w-5 h-5 text-green-600" />
                    <span>Себестоимость:</span>
                  </div>
                  <span class="text-lg font-semibold text-green-700 dark:text-green-400">{{
                    formatCurrency(totalInternal)
                  }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <div class="flex items-center gap-2 text-gray-500">
                    <LucideReceipt class="w-5 h-5 text-blue-600" />
                    <span>Продажная стоимость:</span>
                  </div>
                  <span class="text-lg font-semibold text-blue-700 dark:text-blue-400">{{ formatCurrency(totalExternal)
                  }}</span>
                </div>
                <div v-if="estimate.use_internal_price" class="flex justify-between items-center">
                  <div class="flex items-center gap-2 text-gray-500">
                    <LucideArrowUpRight class="w-5 h-5 text-pink-600" />
                    <span>Маржа:</span>
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
                <div v-else class="flex justify-between items-center border-t pt-2 mt-2 dark:border-qe-black2">
                  <div class="flex items-center gap-2 text-gray-700 dark:text-white font-semibold">
                    <LucideCalculator class="w-5 h-5" />
                    <span>Итого:</span>
                  </div>
                  <span class="text-xl font-bold text-gray-800 dark:text-white">{{
                    formatCurrency(totalExternal)
                  }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Примечания -->
        <NotesBlock class="mt-8" :notes="notes" :read-only="estimate.read_only" @add="addNote" @update="updateNote"
          @delete="deleteNote" />

        <!-- Категории и услуги -->
        <div class="mt-8">
          <div v-for="(groupItems, category) in groupedItems" :key="category"
            class="mb-6 border p-6 rounded-2xl bg-white dark:border-qe-black2 dark:bg-qe-black3 shadow-sm">
            <div class="flex items-center justify-center gap-2 mb-3">
              <LucideFolder class="w-6 h-6 text-blue-600" />
              <h3 class="text-lg font-bold text-gray-800 dark:text-white">
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
                <div v-if="estimate.use_internal_price"
                  class="flex justify-between text-sm text-gray-600 dark:text-gray-300 mt-2">
                  <span>Внутр. цена за единицу:</span>
                  <span>{{ formatCurrency(item.internal_price) }}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>Внешн. цена за единицу:</span>
                  <span>{{ formatCurrency(item.external_price) }}</span>
                </div>
                <div v-if="estimate.use_internal_price"
                  class="flex justify-between font-semibold text-sm text-gray-900 dark:text-white">
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
              <div v-if="estimate.use_internal_price"
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

            <span class="flex items-center gap-2">
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
                  <button :disabled="!log.details || !log.details.length" @click="toggleDetails(log.id)"
                    class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded text-blue-600 hover:bg-blue-50 transition -mr-6 disabled:opacity-50 disabled:cursor-not-allowed">
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
                    <template v-if="typeof d === 'string'">
                      <span class="font-semibold">{{ d }}</span>
                    </template>
                    <template v-else>
                      <!-- Удаление -->
                      <span v-if="d.label && d.old && !d.new">
                        <span class="font-semibold">{{ d.label }}:</span>
                        <span v-if="isDate(d.old)" class="mx-1 text-gray-500 line-through">
                          {{ formatLogDate(d.old) }}
                        </span>
                        <span v-else class="mx-1 text-gray-500 line-through">{{ d.old }}</span>
                      </span>
                      <!-- Добавление -->
                      <span v-else-if="d.label && d.new && !d.old">
                        <span class="font-semibold">{{ d.label }}:</span>
                        <span v-if="isDate(d.new)" class="mx-1 text-blue-700 dark:text-blue-400 font-semibold">
                          {{ formatLogDate(d.new) }}
                        </span>
                        <span v-else class="mx-1 text-blue-700 dark:text-blue-400 font-semibold">{{ d.new }}</span>
                      </span>
                      <!-- Изменение -->
                      <span v-else>
                        <span class="font-semibold">{{ d.label }}:</span>

                        <span v-if="isDate(d.old)" class="mx-1 text-gray-500 line-through">
                          {{ formatLogDate(d.old) }}
                        </span>
                        <span v-else class="mx-1 text-gray-500 line-through">{{ d.old }}</span>
                        <span v-if="isDate(d.new)" class="-mx-1 -mr-2 text-blue-700 dark:text-blue-400 font-semibold">
                          → {{ formatLogDate(d.new) }}
                        </span>
                        <span v-else class="-mx-1 -mr-2 text-blue-700 dark:text-blue-400 font-semibold"> → {{ d.new
                        }}</span>
                      </span>
                    </template>
                  </li>
                </ul>
              </transition>
            </div>
          </div>
          <QePagination :total="logTotal" :per-page="10" :page="logPage" @update:page="changeLogPage" class="mt-2" />
        </div>

        <div v-if="versions.length" class="mt-2 pt-6 text-sm">
          <h3 class="font-semibold mb-4">
            <span class="flex items-center gap-2">
              <GitCommitVertical class="w-5 h-5 text-blue-600" />
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
          <QePagination :total="versionTotal" :per-page="10" :page="versionPage" @update:page="changeVersionPage"
            class="mt-2" />
        </div>
      </div>
    </div>
    <transition name="modal-fade">
      <div v-if="showSendModal" class="fixed inset-0 z-50 flex items-center justify-center px-4">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeSendModal" />
        <div
          class="relative z-10 w-full max-w-xl rounded-2xl bg-white dark:bg-qe-black2 shadow-2xl border border-gray-200 dark:border-qe-black3 p-6">
          <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">Отправка сметы по email</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">Email получателя</label>
              <input v-model.trim="sendForm.to" type="email" class="qe-input w-full" placeholder="client@example.com" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">Тема письма</label>
              <input v-model.trim="sendForm.subject" type="text" class="qe-input w-full"
                placeholder="Смета для согласования" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">Текст письма</label>
              <textarea v-model.trim="sendForm.message" rows="5" class="qe-input w-full resize-y"
                placeholder="Введите текст письма" />
            </div>
            <div class="flex flex-wrap items-center gap-4">
              <label class="inline-flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
                <input v-model="sendForm.attach_pdf" type="checkbox" class="rounded border-gray-300" />
                <span>PDF</span>
              </label>
              <label class="inline-flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
                <input v-model="sendForm.attach_excel" type="checkbox" class="rounded border-gray-300" />
                <span>Excel</span>
              </label>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button class="qe-btn-secondary" @click="closeSendModal" :disabled="isSending">Отмена</button>
            <button class="qe-btn-success" @click="sendEstimateEmail" :disabled="!canSendEstimate || isSending">
              {{ isSending ? "Отправка..." : "Отправить" }}
            </button>
          </div>
        </div>
      </div>
    </transition>
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
import { useNotesStore } from "@/store/notes";
import { onClickOutside } from "@vueuse/core";
import { useToast } from "vue-toastification";
import QeModal from "@/components/QeModal.vue";
import QePagination from "@/components/QePagination.vue";
import NotesBlock from "@/components/NotesBlock.vue";
import fileDownload from "js-file-download";

import {
  LucideFileText,
  LucideUser,
  Undo2,
  Info,
  RotateCcw,
  LucideCalendar,
  LucideUserCircle,
  LucideMapPin,
  LucidePercentCircle,
  ClipboardPaste,
  LucideTrash2,
  Download,
  LucideClock3,
  LucideRefreshCw,
  LucideWallet,
  LucideHistory,
  LucidePiggyBank,
  LucideReceipt,
  GitCommitVertical,
  LucideArrowUpRight,
  LucideCalculator,
  LucideFolder,
  MoreHorizontal,
} from "lucide-vue-next";



const route = useRoute();
const router = useRouter();
const store = useEstimatesStore();
const notesStore = useNotesStore();
const toast = useToast();

const versionParam = computed(() =>
  route.query.version ? Number(route.query.version) : null,
);
const isVersionView = computed(() => versionParam.value !== null);
const currentVersion = ref(null);

const showExport = ref(false);
const menuRef = ref(null);
const showActionsMenu = ref(false);
const actionsMenuRef = ref(null);
const showConfirm = ref(false);
const showSendModal = ref(false);
const isSending = ref(false);
const sendForm = ref({
  to: "",
  subject: "",
  message: "",
  attach_pdf: true,
  attach_excel: true,
});

const estimate = ref(null);
const notes = ref([]);
const logs = ref([]);
const versions = ref([]);
const logTotal = ref(0);
const versionTotal = ref(0);
const logPage = ref(1);
const versionPage = ref(1);
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

    logPage.value = 1;
    versionPage.value = 1;

    const logRes = await store.getEstimateLogs(id, { page: logPage.value, limit: 10 });
    logs.value = logRes.items;
    logTotal.value = logRes.total;
    const verRes = await store.getEstimateVersions(id, { page: versionPage.value, limit: 10 });
    versions.value = verRes.items;
    versionTotal.value = verRes.total;
    notes.value = await notesStore.fetchEstimateNotes(id);
    error.value = null;
  } catch (e) {
    if (e.response?.status === 404) error.value = "❌ Смета не найдена.";
    else if (e.response?.status === 403) error.value = "🚫 Нет доступа.";
    else error.value = "⚠️ Ошибка загрузки.";
  }
}

function isDate(val) {
  if (!val) return false;
  if (val instanceof Date) return true;
  // Очень примитивно: ISO date string содержит 'T', обычно длинная
  return (
    typeof val === "string" &&
    val.length >= 10 && // минимальная длина для ISO/русской даты
    (
      val.includes('T') ||           // ISO ("2025-06-19T13:43:00Z")
      val.match(/^\d{4}-\d{2}-\d{2}/) // "2025-06-19"
    ) &&
    !isNaN(Date.parse(val))
  );
}

function formatLogDate(dt) {
  if (!dt) return "—";
  const date = typeof dt === "string" ? new Date(dt) : dt;
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(loadAll);
watch(() => route.query.version, loadAll);
watch(() => route.params.id, loadAll);

onUnmounted(() => {
  store.currentEstimate = null;
});

onClickOutside(menuRef, () => {
  showExport.value = false;
});
onClickOutside(actionsMenuRef, () => {
  showActionsMenu.value = false;
});

function confirmDelete() {
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
  showConfirm.value = true;
}

function onActionMenuClick(handler) {
  showActionsMenu.value = false;
  handler();
}

function goToEdit() {
  if (!estimate.value) return;
  router.push(`/estimates/${estimate.value.id}/edit`);
}

const canSendEstimate = computed(
  () =>
    !!sendForm.value.to &&
    !!sendForm.value.message &&
    (sendForm.value.attach_pdf || sendForm.value.attach_excel),
);

function openSendModal() {
  if (!estimate.value) return;
  sendForm.value = {
    to: estimate.value.client?.email || "",
    subject: `Смета: ${estimate.value.name}`,
    message: `Здравствуйте!\n\nНаправляю смету «${estimate.value.name}» во вложении.`,
    attach_pdf: true,
    attach_excel: true,
  };
  showSendModal.value = true;
}

function closeSendModal() {
  if (isSending.value) return;
  showSendModal.value = false;
}

async function changeLogPage(p) {
  logPage.value = p;
  const res = await store.getEstimateLogs(route.params.id, { page: p, limit: 10 });
  logs.value = res.items;
  logTotal.value = res.total;
}

async function changeVersionPage(p) {
  versionPage.value = p;
  const res = await store.getEstimateVersions(route.params.id, { page: p, limit: 10 });
  versions.value = res.items;
  versionTotal.value = res.total;
}

async function toggleReadOnly() {
  if (!estimate.value) return;
  try {
    const updated = await store.setEstimateReadOnly(estimate.value.id, !estimate.value.read_only);
    estimate.value = updated;
    toast.success(updated.read_only ? "Смета переведена в режим только чтение" : "Режим редактирования восстановлен");
    await changeLogPage(logPage.value);
  } catch (e) {
    console.error(e);
    const detail = e?.response?.data?.detail;
    toast.error(typeof detail === "string" ? detail : "Не удалось изменить режим сметы");
  }
}

async function copyEstimate() {
  const original = await store.getEstimateById(estimate.value.id);
  store.setCopiedEstimate(original);
  router.push({ path: "/estimates/create", query: { copy: "1" } });
}

async function copyVersion() {
  if (!estimate.value) return;
  store.setCopiedEstimate(estimate.value);
  router.push({ path: "/estimates/create", query: { copy: "1" } });
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
    estimate.value?.use_internal_price
      ? estimate.value.items?.reduce((sum, item) => sum + getItemInternal(item), 0) || 0
      : 0,
);
const totalExternal = computed(
  () =>
    estimate.value?.items?.reduce(
      (sum, item) => sum + getItemExternal(item),
      0,
    ) || 0,
);

const totalDiff = computed(() =>
  estimate.value?.use_internal_price ? totalExternal.value - totalInternal.value : 0
);

const vat = computed(() =>
  estimate.value?.vat_enabled
    ? totalExternal.value * (estimate.value.vat_rate / 100)
    : 0,
);
const totalWithVat = computed(() => totalExternal.value + vat.value);

async function addNote(text) {
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
  try {
    const n = await notesStore.addEstimateNote(route.params.id, text);
    notes.value.unshift(n);
    const res = await store.getEstimateLogs(route.params.id, { page: logPage.value, limit: 10 });
    logs.value = res.items;
    logTotal.value = res.total;
  } catch (e) {
    const detail = e?.response?.data?.detail;
    toast.error(typeof detail === "string" ? detail : "Не удалось добавить примечание");
  }
}

async function updateNote(payload) {
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
  try {
    const n = await notesStore.updateNote(payload.id, payload.text);
    const idx = notes.value.findIndex((x) => x.id === payload.id);
    if (idx !== -1) notes.value[idx] = n;
    const res = await store.getEstimateLogs(route.params.id, { page: logPage.value, limit: 10 });
    logs.value = res.items;
    logTotal.value = res.total;
  } catch (e) {
    const detail = e?.response?.data?.detail;
    toast.error(typeof detail === "string" ? detail : "Не удалось обновить примечание");
  }
}

async function deleteNote(id) {
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
  try {
    await notesStore.deleteNote(id);
    notes.value = notes.value.filter((n) => n.id !== id);
    const res = await store.getEstimateLogs(route.params.id, { page: logPage.value, limit: 10 });
    logs.value = res.items;
    logTotal.value = res.total;
  } catch (e) {
    const detail = e?.response?.data?.detail;
    toast.error(typeof detail === "string" ? detail : "Не удалось удалить примечание");
  }
}

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

async function sendEstimateEmail() {
  if (!estimate.value || !canSendEstimate.value || isSending.value) return;

  try {
    isSending.value = true;
    await store.sendEstimateByEmail(estimate.value.id, {
      to: sendForm.value.to,
      subject: sendForm.value.subject,
      message: sendForm.value.message,
      attach_pdf: sendForm.value.attach_pdf,
      attach_excel: sendForm.value.attach_excel,
    });
    toast.success("Смета успешно отправлена");
    showSendModal.value = false;
    await changeLogPage(logPage.value);
  } catch (e) {
    console.error(e);
    const detail = e?.response?.data?.detail;
    toast.error(typeof detail === "string" ? detail : "Не удалось отправить смету");
  } finally {
    isSending.value = false;
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
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
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
  if (estimate.value?.read_only) {
    toast.error("Смета в режиме только чтение");
    return;
  }
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

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
