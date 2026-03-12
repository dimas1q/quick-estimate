import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    users: [],
    usersTotal: 0
  }),

  actions: {
    async fetchUsers(params = {}) {
      const res = await axios.get('/admin/users', { params })
      this.users = res.data.items
      this.usersTotal = res.data.total
      return res.data
    },

    async getUser(userId) {
      const res = await axios.get(`/admin/users/${userId}`)
      return res.data
    },

    async updateUserProfile(userId, payload) {
      const res = await axios.put(`/admin/users/${userId}`, payload)
      return res.data
    },

    async updateUserRole(userId, isAdmin) {
      const res = await axios.patch(`/admin/users/${userId}/role`, { is_admin: isAdmin })
      return res.data
    },

    async updateUserActivation(userId, isActive) {
      const res = await axios.patch(`/admin/users/${userId}/activation`, { is_active: isActive })
      return res.data
    },

    async fetchUserClients(userId, params = {}) {
      const res = await axios.get(`/admin/users/${userId}/clients`, { params })
      return res.data
    },

    async createUserClient(userId, payload) {
      const res = await axios.post(`/admin/users/${userId}/clients`, payload)
      return res.data
    },

    async updateUserClient(userId, clientId, payload) {
      const res = await axios.put(`/admin/users/${userId}/clients/${clientId}`, payload)
      return res.data
    },

    async deleteUserClient(userId, clientId) {
      await axios.delete(`/admin/users/${userId}/clients/${clientId}`)
    },

    async fetchUserTemplates(userId, params = {}) {
      const res = await axios.get(`/admin/users/${userId}/templates`, { params })
      return res.data
    },

    async createUserTemplate(userId, payload) {
      const res = await axios.post(`/admin/users/${userId}/templates`, payload)
      return res.data
    },

    async updateUserTemplate(userId, templateId, payload) {
      const res = await axios.put(`/admin/users/${userId}/templates/${templateId}`, payload)
      return res.data
    },

    async deleteUserTemplate(userId, templateId) {
      await axios.delete(`/admin/users/${userId}/templates/${templateId}`)
    },

    async fetchUserEstimates(userId, params = {}) {
      const res = await axios.get(`/admin/users/${userId}/estimates`, { params })
      return res.data
    },

    async createUserEstimate(userId, payload) {
      const res = await axios.post(`/admin/users/${userId}/estimates`, payload)
      return res.data
    },

    async updateUserEstimate(userId, estimateId, payload) {
      const res = await axios.put(`/admin/users/${userId}/estimates/${estimateId}`, payload)
      return res.data
    },

    async deleteUserEstimate(userId, estimateId) {
      await axios.delete(`/admin/users/${userId}/estimates/${estimateId}`)
    }
  }
})
