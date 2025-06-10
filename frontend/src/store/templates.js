// src/store/templates.js
import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useTemplatesStore = defineStore('templates', {
  state: () => ({
    templates: [],
    importedTemplate: null,
    pagination: { total: 0, limit: 20, offset: 0 }
  }),

  actions: {
    async fetchTemplates(params = {}) {
      const res = await axios.get('/templates/', { params })
      this.templates = res.data.items
      this.pagination = res.data.meta
    },

    async createTemplate(data) {
      const res = await axios.post('/templates/', data)
      await this.fetchTemplates()
      return res.data
    },

    async getTemplateById(id) {
      const res = await axios.get(`/templates/${id}`)
      return res.data
    },

    async deleteTemplate(id) {
      await axios.delete(`/templates/${id}`)
      await this.fetchTemplates()
    },

    async updateTemplate(id, data) {
      const res = await axios.put(`/templates/${id}`, data)
      await this.fetchTemplates()
      return res.data
    },
    
    async exportTemplate(id) {
      const res = await axios.get(`/templates/${id}`)
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `${res.data.name || 'template'}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  }
})
