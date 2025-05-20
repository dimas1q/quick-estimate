import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useEstimatesStore = defineStore('estimates', {
  state: () => ({
    estimates: [],
    copiedEstimate: null,
    importedEstimate: null
  }),

  actions: {
    
    async fetchEstimates(params = {}) {
      const res = await axios.get('/estimates/', { params })
      this.estimates = res.data
    },

    async createEstimate(data) {
      const res = await axios.post('/estimates/', data)
      this.fetchEstimates() 
      return res.data 
    },

    async getEstimateById(id) {
      const res = await axios.get(`/estimates/${id}`)
      return res.data
    },

    async deleteEstimate(id) {
      await axios.delete(`/estimates/${id}/`)
      this.fetchEstimates()
    },

    async updateEstimate(id, data) {
      const res = await axios.put(`/estimates/${id}/`, data)
      await this.fetchEstimates()
      return res.data
    },

    async getEstimateVersion(versionId, estimateId) {
      const res = await axios.get(`/versions/${versionId}`, {
        params: { estimate_id: estimateId }
      })
      return res.data
    },

    async getEstimateVersions(estimateId) {
      const res = await axios.get('/versions', {
        params: { estimate_id: estimateId }
      })
      return res.data
    },

    async restoreVersion(versionId, estimateId) {
      await axios.post(`/versions/${versionId}/restore/`, null, {
        params: { estimate_id: estimateId }
      })
    },

    async deleteVersion(versionId, estimateId) {
      await axios.delete(`/versions/${versionId}/`, {
        params: { estimate_id: estimateId }
      })
    },

    async exportEstimate(id) {
      const res = await axios.get(`/estimates/${id}`)
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

    async downloadEstimatePdf(id) {
      const res = await axios.get(`/estimates/${id}/export/pdf`, {
        responseType: 'blob'
      })
      return res.data
    },

    async downloadEstimateExcel(id) {
      const res = await axios.get(`/estimates/${id}/export/excel`, {
        responseType: 'blob'
      })
      return res.data
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
      const res = await axios.get(`/estimates/${id}/logs`)
      return res.data
    }
    
  }
})
