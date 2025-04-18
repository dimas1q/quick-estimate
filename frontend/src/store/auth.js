import { defineStore } from 'pinia'
import { useEstimatesStore } from '@/store/estimates'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || null,
        user: null
    }),

    actions: {
        async login(identifier, password) {
            const res = await axios.post('http://localhost:8000/api/auth/login',
                new URLSearchParams({ username: identifier, password })
            )

            this.token = res.data.access_token
            localStorage.setItem('token', this.token)
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

            await this.fetchUser()
        },

        async register({ login, email, password }) {
            await axios.post('http://localhost:8000/api/auth/register', {
                login,
                email,
                password
            })
        },

        async fetchUser() {
            const res = await axios.get('http://localhost:8000/api/auth/me', {
                headers: {
                    Authorization: `Bearer ${this.token}`
                }
            })
            this.user = res.data

            // Восстановим дефолтный токен, если вдруг axios сбросился
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
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
