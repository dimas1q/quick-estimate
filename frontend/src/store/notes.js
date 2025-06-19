import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useNotesStore = defineStore('notes', {
  actions: {
    async fetchEstimateNotes(id) {
      const res = await axios.get(`/notes/estimates/${id}/`)
      return res.data
    },
    async fetchClientNotes(id) {
      const res = await axios.get(`/notes/clients/${id}/`)
      return res.data
    },
    async fetchTemplateNotes(id) {
      const res = await axios.get(`/notes/templates/${id}/`)
      return res.data
    },
    async addEstimateNote(id, text) {
      const res = await axios.post(`/notes/estimates/${id}/`, { text })
      return res.data
    },
    async addClientNote(id, text) {
      const res = await axios.post(`/notes/clients/${id}/`, { text })
      return res.data
    },
    async addTemplateNote(id, text) {
      const res = await axios.post(`/notes/templates/${id}/`, { text })
      return res.data
    },
    async updateNote(id, text) {
      const res = await axios.put(`/notes/${id}`, { text })
      return res.data
    },
    async deleteNote(id) {
      await axios.delete(`/notes/${id}`)
    }
  }
})
