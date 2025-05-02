import { defineStore } from 'pinia'
import axios from 'axios'

export const useClientsStore = defineStore('clients', {
    state: () => ({
        clients: []
    }),
    actions: {
        async fetchClients(params = {}) {
            const res = await axios.get('http://localhost:8000/api/clients/', { params })
            this.clients = res.data
        },
        async getClientById(id) {
            const res = await axios.get(`http://localhost:8000/api/clients/${id}`)
            return res.data
        },
        async createClient(data) {
            const res = await axios.post('http://localhost:8000/api/clients', data)
            await this.fetchClients()
            return res.data
        },
        async updateClient(id, data) {
            const res = await axios.put(`http://localhost:8000/api/clients/${id}`, data)
            await this.fetchClients()
            return res.data
        },
        async deleteClient(id) {
            await axios.delete(`http://localhost:8000/api/clients/${id}`)
            await this.fetchClients()
        }
    }
})
