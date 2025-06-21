import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useAnalyticsStore = defineStore('analytics', {
    state: () => ({
        global: null,
        client: null,
    }),

    actions: {
        /**
         * Загружает глобальную аналитику.
         * @param {Object} params Параметры фильтрации: 
         *   start_date, end_date, status[], vat_enabled, categories[], granularity
         */
        async fetchGlobal(params = {}) {
            const res = await axios.get('/analytics/', { params })
            this.global = res.data
            return res.data
        },

        /**
         * Загружает аналитику по конкретному клиенту.
         * @param {number} clientId ID клиента
         * @param {Object} params Параметры фильтрации (как в глобальной)
         */
        async fetchClient(clientId, params = {}) {
            const res = await axios.get(`/analytics/clients/${clientId}`, { params })
            this.client = res.data
            return res.data
        },

        /**
         * Скачивает аналитику в заданном формате.
         * @param {number|null} clientId ID клиента или null
         * @param {Object} params Параметры фильтрации
         * @param {'csv'|'pdf'|'excel'} format Формат файла
         */
        async downloadAnalytics(clientId = null, params = {}, format = 'csv') {
            const query = { ...params, format }
            if (clientId) query.client_id = clientId
            const res = await axios.get('/analytics/export', {
                params: query,
                responseType: 'blob',
            })
            return res.data
        },
    },
})
