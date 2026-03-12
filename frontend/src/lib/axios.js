import axios from 'axios'
import { appRuntimeConfig } from '@/config/runtime'
import { normalizeApiError } from '@/lib/api-error'

axios.defaults.baseURL = appRuntimeConfig.apiUrl

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    error.qe = normalizeApiError(error)
    return Promise.reject(error)
  }
)

export default axios
