const runtimeConfig = typeof window !== 'undefined' ? window.__QE_CONFIG__ || {} : {}

function readString(value, fallback = '') {
  if (typeof value !== 'string') return fallback
  return value.trim()
}

export const appRuntimeConfig = Object.freeze({
  apiUrl: readString(runtimeConfig.apiUrl, readString(import.meta.env.VITE_API_URL, '/api')),
  googleClientId: readString(
    runtimeConfig.googleClientId,
    readString(import.meta.env.VITE_GOOGLE_CLIENT_ID, '')
  )
})
