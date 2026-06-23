import { createReadStream, existsSync } from 'node:fs'
import { stat } from 'node:fs/promises'
import http, { createServer } from 'node:http'
import https from 'node:https'
import { extname, join, normalize } from 'node:path'

const host = process.env.HOST || '0.0.0.0'
const port = Number(process.env.PORT || 5173)
const distRoot = join(process.cwd(), 'dist')
const apiTarget = normalizeTarget(process.env.API_PROXY_TARGET || 'http://backend:8000')
const minioTarget = normalizeTarget(process.env.MINIO_PROXY_TARGET || 'http://minio:9000')
const proxyPrefixes = ['/api/', '/rag-documents/', '/rag-parsed/', '/rag-preview/']

const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
}

function normalizeTarget(value) {
  return value.endsWith('/') ? value.slice(0, -1) : value
}

function proxyTargetFor(pathname) {
  if (pathname.startsWith('/api/')) return apiTarget
  if (proxyPrefixes.some((prefix) => pathname.startsWith(prefix))) return minioTarget
  return null
}

function sendError(response, statusCode, message) {
  response.writeHead(statusCode, { 'Content-Type': 'text/plain; charset=utf-8' })
  response.end(message)
}

function staticPath(pathname) {
  const safePath = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, '')
  const resolved = join(distRoot, safePath)
  return resolved.startsWith(distRoot) ? resolved : join(distRoot, 'index.html')
}

async function serveStatic(request, response, pathname) {
  let filePath = staticPath(pathname === '/' ? '/index.html' : pathname)
  if (!existsSync(filePath)) filePath = join(distRoot, 'index.html')

  try {
    const fileStat = await stat(filePath)
    if (!fileStat.isFile()) filePath = join(distRoot, 'index.html')
    const ext = extname(filePath)
    response.writeHead(200, {
      'Content-Type': contentTypes[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable'
    })
    createReadStream(filePath).pipe(response)
  } catch (error) {
    sendError(response, 404, 'Not found')
  }
}

function proxyRequest(request, response, target) {
  const upstreamUrl = new URL(request.url || '/', target)
  const headers = { ...request.headers, host: upstreamUrl.host }
  delete headers.connection
  delete headers['content-length']
  const client = upstreamUrl.protocol === 'https:' ? https : http

  const upstreamRequest = client.request(
    upstreamUrl,
    {
      method: request.method,
      headers,
      timeout: 120_000
    },
    (upstreamResponse) => {
      response.writeHead(upstreamResponse.statusCode || 502, upstreamResponse.headers)
      upstreamResponse.pipe(response)
    }
  )

  upstreamRequest.on('timeout', () => {
    upstreamRequest.destroy(new Error('upstream timeout'))
  })
  upstreamRequest.on('error', (error) => {
    if (response.headersSent) {
      response.destroy(error)
      return
    }
    sendError(response, 502, `Proxy error: ${error instanceof Error ? error.message : 'unknown error'}`)
  })
  request.pipe(upstreamRequest)
}

const server = createServer(async (request, response) => {
  const url = new URL(request.url || '/', 'http://localhost')
  const target = proxyTargetFor(url.pathname)
  if (target) {
    proxyRequest(request, response, target)
    return
  }
  await serveStatic(request, response, url.pathname)
})

server.listen(port, host, () => {
  console.log(`Frontend server listening on http://${host}:${port}`)
})
