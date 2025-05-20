import axios from 'axios'       // ✅ Чистый импорт без цикла

// глобальная настройка базового URL
axios.defaults.baseURL = import.meta.env.VITE_API_URL

export default axios
