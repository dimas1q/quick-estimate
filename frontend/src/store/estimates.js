import { defineStore } from 'pinia'
import axios from 'axios'

export const useEstimatesStore = defineStore('estimates', {
  state: () => ({
    estimates: [],
    copiedEstimate: null,
    importedEstimate: null
  }),

  actions: {
    
    async fetchEstimates(params = {}) {
      const res = await axios.get('http://localhost:8000/api/estimates/', { params })
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
    },

    async exportEstimate(id) {
      const res = await axios.get(`http://localhost:8000/api/estimates/${id}`)
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `${res.data.name || 'estimate'}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    },

    setCopiedEstimate(estimate) {
      this.copiedEstimate = estimate
    },

    setImportedEstimate(data) {
      this.importedEstimate = data
    },

    clearCopiedEstimate() {
      this.copiedEstimate = null
    },

    getEstimateLogs: async function (id) {
      const res = await axios.get(`http://localhost:8000/api/estimates/${id}/logs`)
      return res.data
    }
    
  }
})
