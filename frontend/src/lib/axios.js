import axios from 'axios'
import { appRuntimeConfig } from '@/config/runtime'

axios.defaults.baseURL = appRuntimeConfig.apiUrl

export default axios
