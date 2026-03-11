# QuickEstimate Frontend

Frontend часть QuickEstimate: Vue 3 + Vite + Pinia + Tailwind.

## Что реализовано
- SPA с роутингом (auth, сметы, шаблоны, клиенты, аналитика, профиль).
- Pinia stores для основных доменов: `auth`, `estimates`, `templates`, `clients`, `analytics`, `notes`.
- Формы создания/редактирования смет, шаблонов, клиентов.
- Экспорт/импорт в рамках текущего UI-flow (без backend import endpoint).
- Тёмная тема и адаптивные layout-ы.

## Ограничения текущей реализации
- OAuth логин отсутствует.
- Полноценный admin UI отсутствует.
- Autosave и read-only режим смет отсутствуют.
- Фильтр по статусу в `src/pages/estimate/EstimatesPage.vue` содержит дефект сериализации.
- Списки клиентов/шаблонов в формах могут быть неполными (backend default pagination `limit=5`, store-запросы часто без `limit`).

## Команды

Установка зависимостей:
```bash
npm install
```

Запуск dev-сервера:
```bash
npm run dev
```

Сборка:
```bash
npm run build
```

Preview сборки:
```bash
npm run preview
```

## Важный нюанс по lockfile

На текущем состоянии `npm ci` падает с `EUSAGE`, потому что `package.json` и `package-lock.json` не синхронизированы (в lockfile отсутствуют platform-specific зависимости `esbuild/rollup`).

До нормализации lockfile используйте `npm install` для локальной разработки.

## Конфигурация API

`src/lib/axios.js` использует:
- `import.meta.env.VITE_API_URL`

Для локального запуска обычно используется API:
- `http://localhost:8000/api`
