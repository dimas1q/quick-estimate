import { defineStore } from 'pinia'
import axios from 'axios'

export const useEstimatesStore = defineStore('estimates', {
  state: () => ({
    estimates: [],
  }),

  actions: {
    async fetchEstimates() {
      const res = await axios.get('http://localhost:8000/api/estimates/')
      this.estimates = res.data
    },

    async createEstimate(data) {
      const res = await axios.post('http://localhost:8000/api/estimates/', data)
      this.fetchEstimates() // необязательно, но можно
      return res.data // для получения id
    },

    async getEstimateById(id) {
      const res = await axios.get(`http://localhost:8000/api/estimates/${id}`)
      return res.data
    },

    async deleteEstimate(id) {
      await axios.delete(`http://localhost:8000/api/estimates/${id}`)
      this.fetchEstimates()
    },

    async updateEstimate(id, data) {
      const res = await axios.put(`http://localhost:8000/api/estimates/${id}`, data)
      await this.fetchEstimates()
      return res.data
    }
    
  }
})
