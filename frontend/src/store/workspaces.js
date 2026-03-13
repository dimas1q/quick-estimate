import { defineStore } from 'pinia'
import axios from '@/lib/axios'

export const useWorkspacesStore = defineStore('workspaces', {
  state: () => ({
    current: null,
    members: [],
    invitations: [],
    incomingInvitations: []
  }),

  actions: {
    async fetchCurrent() {
      const res = await axios.get('/workspaces/current')
      this.current = res.data
      return this.current
    },

    async fetchMembers() {
      const res = await axios.get('/workspaces/current/members')
      this.members = Array.isArray(res.data) ? res.data : []
      return this.members
    },

    async updateMemberRole(userId, role) {
      const res = await axios.patch(`/workspaces/current/members/${userId}/role`, {
        role
      })
      const updated = res.data
      this.members = this.members.map((member) =>
        member.user_id === updated.user_id ? updated : member
      )
      return updated
    },

    async removeMember(userId) {
      await axios.delete(`/workspaces/current/members/${userId}`)
      this.members = this.members.filter((member) => member.user_id !== userId)
    },

    async transferOwnership(newOwnerUserId) {
      const res = await axios.post('/workspaces/current/transfer-ownership', {
        new_owner_user_id: newOwnerUserId
      })
      this.current = res.data
      return this.current
    },

    async deleteWorkspace(confirmName) {
      await axios.delete('/workspaces/current', {
        data: { confirm_name: confirmName }
      })
      this.current = null
      this.members = []
      this.invitations = []
    },

    async fetchInvitations() {
      const res = await axios.get('/workspaces/current/invitations')
      this.invitations = Array.isArray(res.data) ? res.data : []
      return this.invitations
    },

    async fetchIncomingInvitations() {
      const res = await axios.get('/workspaces/invitations/incoming')
      this.incomingInvitations = Array.isArray(res.data) ? res.data : []
      return this.incomingInvitations
    },

    async createInvitation(payload) {
      const res = await axios.post('/workspaces/current/invitations', payload)
      const data = res.data
      if (data?.invitation) {
        this.invitations = [data.invitation, ...this.invitations]
      }
      return data
    },

    async revokeInvitation(invitationId) {
      await axios.delete(`/workspaces/current/invitations/${invitationId}`)
      this.invitations = this.invitations.map((invite) =>
        invite.id === invitationId ? { ...invite, status: 'revoked' } : invite
      )
    },

    async acceptIncomingInvitation(invitationId) {
      const res = await axios.post(`/workspaces/invitations/${invitationId}/accept`)
      this.incomingInvitations = this.incomingInvitations.filter(
        (invite) => invite.id !== invitationId
      )
      return res.data
    },

    async rejectIncomingInvitation(invitationId) {
      const res = await axios.post(`/workspaces/invitations/${invitationId}/reject`)
      this.incomingInvitations = this.incomingInvitations.filter(
        (invite) => invite.id !== invitationId
      )
      return res.data
    },

    async createWorkspace(payload) {
      const res = await axios.post('/workspaces', payload)
      this.current = res.data
      return res.data
    },

    async updateCurrentWorkspace(payload) {
      const res = await axios.patch('/workspaces/current', payload)
      this.current = res.data
      return res.data
    }
  }
})
