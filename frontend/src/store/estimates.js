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
      await axios.post('http://localhost:8000/api/estimates/', data)
      await this.fetchEstimates()
    },

    async createEstimate(data) {
      const res = await axios.post('http://localhost:8000/api/estimates/', data)
      this.fetchEstimates() // необязательно, но можно
      return res.data // для получения id
    }
    
  }
})
