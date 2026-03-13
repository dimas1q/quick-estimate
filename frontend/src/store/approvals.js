import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useApprovalsStore = defineStore('approvals', {
  state: () => ({
    pending: [],
    history: []
  }),

  actions: {
    async fetchMyTasks(scope = 'pending') {
      const res = await axios.get('/approvals/my', {
        params: { scope }
      })
      if (scope === 'pending') this.pending = res.data
      if (scope === 'history') this.history = res.data
      return res.data
    },

    async signStep(stepId, payload) {
      const res = await axios.post(`/approvals/steps/${stepId}/decision`, payload)
      return res.data
    },

    async getEstimatePreview(estimateId) {
      const res = await axios.get(`/approvals/estimates/${estimateId}/preview`)
      return res.data
    }
  }
})
