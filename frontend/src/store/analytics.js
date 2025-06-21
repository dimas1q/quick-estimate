import { defineStore } from 'pinia'
import axios from '@/lib/axios'
import { ref } from 'vue'

export const useAnalyticsStore = defineStore('analytics', () => {
    const global = ref(null)
    const client = ref(null)

    /**
     * Загружает глобальную аналитику.
     * @param {Object} params Параметры фильтрации: 
     *   start_date, end_date, status[], vat_enabled, categories[], granularity
     */
    async function fetchGlobal(params = {}) {
        const res = await axios.get('/analytics/', { params })
        global.value = res.data
        return res.data
    }

    /**
     * Загружает аналитику по конкретному клиенту.
     * @param {number} clientId ID клиента
     * @param {Object} params Параметры фильтрации (как в глобальной)
     */
    async function fetchClient(clientId, params = {}) {
        const res = await axios.get(`/analytics/clients/${clientId}`, { params })
        client.value = res.data
        return res.data
    }

    async function downloadGlobalCsv(params = {}) {
        const res = await axios.get('/analytics/export', {
            params,
            responseType: 'blob'
        })
        return res.data
    }

    async function downloadGlobalPdf(params = {}) {
        const res = await axios.get('/analytics/export', {
            params,
            responseType: 'blob'
        })
        return res.data
    }

    async function downloadGlobalExcel(params = {}) {
        const res = await axios.get('/analytics/export', {
            params,
            responseType: 'blob'
        })
        return res.data
    }

    return {
        global,
        client,
        fetchGlobal,
        fetchClient,
        downloadGlobalCsv,
        downloadGlobalPdf,
        downloadGlobalExcel,
    }
})
