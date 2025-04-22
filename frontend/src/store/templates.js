// src/store/templates.js
import { defineStore } from 'pinia'
import axios from 'axios'

export const useTemplatesStore = defineStore('templates', {
  state: () => ({
    templates: [],
  }),

  actions: {
    async fetchTemplates() {
      const res = await axios.get('http://localhost:8000/api/templates/')
      this.templates = res.data
    },

    async createTemplate(data) {
      const res = await axios.post('http://localhost:8000/api/templates/', data)
      await this.fetchTemplates()
      return res.data
    },

    async getTemplateById(id) {
      const res = await axios.get(`http://localhost:8000/api/templates/${id}`)
      return res.data
    },

    async deleteTemplate(id) {
      await axios.delete(`http://localhost:8000/api/templates/${id}`)
      await this.fetchTemplates()
    },

    async updateTemplate(id, data) {
      const res = await axios.put(`http://localhost:8000/api/templates/${id}`, data)
      await this.fetchTemplates()
      return res.data
    },
  }
})
