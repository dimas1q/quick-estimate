import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useClientsStore = defineStore('clients', {
    state: () => ({
        clients: []
    }),
    actions: {
        async fetchClients(params = {}) {
            const res = await axios.get('/clients/', { params })
            this.clients = res.data
        },
        async getClientById(id) {
            const res = await axios.get(`/clients/${id}`)
            return res.data
        },
        async getClientWithEstimates(id) {
            const resClient = await axios.get(`/clients/${id}`)
            const client = resClient.data

            const resEstimates = await axios.get('/estimates/', {
                params: { client: client.id }
            })
            const estimates = resEstimates.data

            return { client, estimates }
        },
        async createClient(data) {
            const res = await axios.post('/clients/', data)
            await this.fetchClients()
            return res.data
        },
        async updateClient(id, data) {
            const res = await axios.put(`/clients/${id}`, data)
            await this.fetchClients()
            return res.data
        },
        async deleteClient(id) {
            await axios.delete(`/clients/${id}`)
            await this.fetchClients()
        }
    }
})
