function extractDetail(error) {
  return typeof error?.response?.data?.detail === 'string'
    ? error.response.data.detail
    : ''
}

export function isWorkspaceNotSelectedError(error) {
  const status = error?.response?.status
  const detail = extractDetail(error).toLowerCase()

  if (status === 409 && detail.includes('рабочее пространство')) {
    return true
  }

  if (
    status === 403 &&
    (detail.includes('текущему рабочему пространству') || detail.includes('рабочее пространство'))
  ) {
    return true
  }

  return false
}

