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
         * Скачивает глобальную аналитику в указанном формате
         * @param {String} format csv | pdf | excel
         * @param {Object} params Параметры фильтрации как в fetchGlobal
         */
        async downloadGlobal(format = 'csv', params = {}) {
            const res = await axios.get('/analytics/export', {
                params: { format, ...params },
                responseType: 'blob'
            })
            return res.data
        },
    },
})
