import fs from 'node:fs'
import path from 'node:path'

const cwd = process.cwd()
const configCandidates = [
  process.env.APP_CONFIG_FILE,
  path.resolve(cwd, '../config/app.dev.toml'),
  path.resolve(cwd, '../config/app.toml'),
  '/app/config/app.toml'
].filter(Boolean)

const configPath = configCandidates.find((candidate) => fs.existsSync(candidate))
const outputPath = process.env.RUNTIME_CONFIG_OUT || path.resolve(cwd, 'public/runtime-config.js')

function parseValue(raw) {
  const value = raw.trim()
  if (!value) return ''

  if (value.startsWith('[') && value.endsWith(']')) {
    const inner = value.slice(1, -1).trim()
    if (!inner) return []
    return inner
      .split(',')
      .map((item) => item.trim())
      .map((item) => parseValue(item))
      .filter((item) => String(item).trim() !== '')
  }

  if (value.startsWith('"') && value.endsWith('"')) {
    try {
      return JSON.parse(value)
    } catch {
      return value.slice(1, -1)
    }
  }

  return value
}

function readTomlSection(fileContent, sectionName) {
  const section = {}
  let activeSection = ''

  for (const rawLine of fileContent.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue

    const sectionMatch = line.match(/^\[([^\]]+)\]$/)
    if (sectionMatch) {
      activeSection = sectionMatch[1].trim()
      continue
    }

    if (activeSection !== sectionName) continue

    const kv = line.match(/^([A-Za-z0-9_]+)\s*=\s*(.+)$/)
    if (!kv) continue

    section[kv[1]] = parseValue(kv[2])
  }

  return section
}

function deriveApiUrl(appEnv, serverPort) {
  const env = String(appEnv || 'development').toLowerCase()
  const port = Number.parseInt(String(serverPort || ''), 10) || 8000
  if (['dev', 'development', 'local', 'test'].includes(env)) {
    return `http://localhost:${port}/api`
  }
  return '/api'
}

function deriveGoogleClientId(rawId) {
  return String(rawId || '').trim()
}

function renderRuntimeConfig({ apiUrl, googleClientId }) {
  const payload = {
    apiUrl: apiUrl || '/api',
    googleClientId: googleClientId || ''
  }

  return `window.__QE_CONFIG__ = Object.assign({}, window.__QE_CONFIG__ || {}, ${JSON.stringify(payload)});\n`
}

if (!configPath) {
  throw new Error(`Config file not found. Checked: ${configCandidates.join(', ')}`)
}

const tomlContent = fs.readFileSync(configPath, 'utf8')
const appSection = readTomlSection(tomlContent, 'app')
const serverSection = readTomlSection(tomlContent, 'server')
const authSection = readTomlSection(tomlContent, 'auth')
const runtimeConfig = renderRuntimeConfig({
  apiUrl: deriveApiUrl(appSection.env, serverSection.port),
  googleClientId: deriveGoogleClientId(authSection.google_oauth_client_id)
})

fs.mkdirSync(path.dirname(outputPath), { recursive: true })
fs.writeFileSync(outputPath, runtimeConfig, 'utf8')
console.log(`Runtime config generated: ${outputPath}`)
