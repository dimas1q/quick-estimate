// frontend/src/store/auth.js
import { defineStore } from 'pinia'
import { useEstimatesStore } from '@/store/estimates'
import axios from '@/lib/axios'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || null,
        user: null,
        pendingEmail: null
    }),

    actions: {
        async login(identifier, password) {
            try {
                const res = await axios.post(
                    '/auth/login',
                    new URLSearchParams({ username: identifier, password })
                )

                this.token = res.data.access_token
                localStorage.setItem('token', this.token)
                axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

                await this.fetchUser()
            } catch (error) {
                if (
                    error.response?.status === 403 &&
                    error.response.data.detail === 'ACCOUNT_INACTIVE'
                ) {
                    this.pendingEmail = error.response.data.email
                    throw { type: 'inactive' }
                }
                throw error
            }
        },

        async register({ login, email, password }) {
            await axios.post('/auth/register', {
                login,
                email,
                password
            })
            this.pendingEmail = email
        },

        async verifyCode({ email, code }) {
            const res = await axios.post('/auth/verify', { email, code })
            this.token = res.data.access_token
            localStorage.setItem('token', this.token)
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
            await this.fetchUser()
            this.pendingEmail = null
        },

        async resendCode(email) {
            await axios.post('/auth/resend', { email })
        },

        async fetchUser() {
            const res = await axios.get('/users/me', {
                headers: {
                    Authorization: `Bearer ${this.token}`
                }
            })
            this.user = res.data

            // Восстановим дефолтный токен, если вдруг axios сбросился
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        },

        async updateProfile({ login, email, name, company }) {
            try {
              await axios.put('/users/me', { login, email, name, company })
              await this.fetchUser()
            } catch (error) {
              throw error.response?.data?.detail || 'Ошибка при обновлении профиля'
            }
          },
          
          async changePassword({ current_password, new_password, confirm_password }) {
            try {
              await axios.put('/users/me/password', {
                current_password,
                new_password,
                confirm_password
              })
            } catch (error) {
                console.error('[changePassword]', error)
                throw error  // ❗
            }
          },
          

        logout() {
            this.token = null
            this.user = null
            localStorage.removeItem('token')

            delete axios.defaults.headers.common['Authorization']

            const estimateStore = useEstimatesStore()
            estimateStore.estimates = []
        },

        async restoreSession() {
            if (this.token) {
                try {
                    await this.fetchUser()
                } catch {
                    this.logout()
                }
            }
        }
    }
})
