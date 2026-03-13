// frontend/src/store/auth.js
import { defineStore } from 'pinia'
import { useEstimatesStore } from '@/store/estimates'
import axios from '@/lib/axios'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || null,
        refreshToken: localStorage.getItem('refresh_token') || null,
        user: null,
        workspaces: [],
        switchingWorkspace: false,
        loading: true
    }),

    actions: {
        setTokens({ accessToken, refreshToken }) {
            this.token = accessToken
            this.refreshToken = refreshToken || null
            localStorage.setItem('token', this.token)
            if (this.refreshToken) {
                localStorage.setItem('refresh_token', this.refreshToken)
            } else {
                localStorage.removeItem('refresh_token')
            }
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        },

        async login(identifier, password) {
            const res = await axios.post('/auth/login',
                new URLSearchParams({ username: identifier, password })
            )

            this.setTokens({
                accessToken: res.data.access_token,
                refreshToken: res.data.refresh_token
            })

            await this.fetchUser()
        },

        async loginWithGoogle(credential) {
            const res = await axios.post('/auth/oauth/google', { credential })

            this.setTokens({
                accessToken: res.data.access_token,
                refreshToken: res.data.refresh_token
            })

            await this.fetchUser()
        },

        async register({ login, email, password }) {
            await axios.post('/auth/register', {
                login,
                email,
                password
            })
        },

        async verifyCode(email, code) {
            const res = await axios.post('/auth/verify', { email, code })
            this.setTokens({
                accessToken: res.data.access_token,
                refreshToken: res.data.refresh_token
            })
            await this.fetchUser()
        },

        async resendCode(email) {
            await axios.post('/auth/resend', { email })
        },

        async refreshAccessToken() {
            if (!this.refreshToken) {
                throw new Error('no_refresh_token')
            }
            const res = await axios.post('/auth/refresh', {
                refresh_token: this.refreshToken
            })
            this.setTokens({
                accessToken: res.data.access_token,
                refreshToken: res.data.refresh_token
            })
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

            try {
                await this.fetchWorkspaces()
            } catch {
                this.workspaces = []
            }
        },

        async fetchWorkspaces() {
            const res = await axios.get('/users/me/workspaces')
            this.workspaces = res.data || []
            return this.workspaces
        },

        async switchWorkspace(organizationId) {
            this.switchingWorkspace = true
            try {
                await axios.post('/users/me/workspaces/switch', {
                    organization_id: organizationId
                })
                await this.fetchUser()
                return this.user
            } finally {
                this.switchingWorkspace = false
            }
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
            this.refreshToken = null
            this.user = null
            this.workspaces = []
            this.switchingWorkspace = false
            localStorage.removeItem('token')
            localStorage.removeItem('refresh_token')

            delete axios.defaults.headers.common['Authorization']

            const estimateStore = useEstimatesStore()
            estimateStore.estimates = []
        },

        async restoreSession() {
            try {
                if (this.token) {
                    try {
                        await this.fetchUser()
                    } catch (error) {
                        if (error?.response?.status === 401 && this.refreshToken) {
                            await this.refreshAccessToken()
                            await this.fetchUser()
                        } else {
                            throw error
                        }
                    }
                }
            } catch {
                this.logout()
            } finally {
                this.loading = false
            }
        }
    }
})
