function asString(value) {
  return typeof value === 'string' ? value : ''
}

export function normalizeApiError(error) {
  const response = error?.response
  const data = response?.data
  const code = asString(data?.code) || 'unknown_error'
  const detail = data?.detail ?? null
  const meta = data?.meta ?? null
  const status = response?.status ?? null

  return { code, detail, meta, status }
}

export function getApiErrorMessage(error, fallback = 'Произошла ошибка') {
  const normalized = normalizeApiError(error)
  if (typeof normalized.detail === 'string' && normalized.detail.trim()) {
    return normalized.detail
  }

  if (Array.isArray(normalized.detail) && normalized.detail.length > 0) {
    const first = normalized.detail[0]
    if (typeof first === 'string' && first.trim()) {
      return first
    }
    if (typeof first?.msg === 'string' && first.msg.trim()) {
      return first.msg
    }
  }

  return fallback
}
