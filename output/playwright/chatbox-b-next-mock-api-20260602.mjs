import http from 'node:http'

const port = Number(process.env.PORT ?? 8022)
let streamAttempts = 0
let conversationReady = false

const promptText = '请联网检索 Kimi 当前公开入口并给出来源'
const answerText = '已根据公开网页来源整理入口：[ref_1]。'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
}

const json = (response, status, body) => {
  response.writeHead(status, {
    ...corsHeaders,
    'Content-Type': 'application/json; charset=utf-8',
  })
  response.end(JSON.stringify(body))
}

const sseEvent = (name, data) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`

const envelope = (type, payload) => ({
  schema_version: 'chat.run.v1',
  type,
  payload,
})

const conversations = () =>
  conversationReady
    ? [
        {
          id: 'c1',
          title: 'Kimi 公开入口',
          updated_at: '2026-06-02T10:00:00Z',
          messages: [
            {
              id: 'student-smoke-1',
              role: 'student',
              content: promptText,
              created_at: '2026-06-02T10:00:00Z',
            },
            {
              id: 'assistant-smoke-1',
              role: 'assistant',
              content: answerText,
              created_at: '2026-06-02T10:00:01Z',
            },
          ],
        },
      ]
    : []

const streamBody = () =>
  [
    sseEvent('conversation', { conversationId: 'c1' }),
    sseEvent('run_started', envelope('run_started', { conversationId: 'c1', messageId: 'assistant-smoke-1' })),
    sseEvent(
      'source',
      envelope('source', {
        sourceId: 'source-1',
        dedupeKey: 'https://kimi.moonshot.cn/',
        displayTitle: 'kimi.moonshot.cn',
        title: 'kimi.moonshot.cn',
        url: 'https://kimi.moonshot.cn/',
        hostname: 'kimi.moonshot.cn',
        trustLabel: 'Public web source',
      }),
    ),
    sseEvent(
      'source',
      envelope('source', {
        sourceId: 'source-2',
        dedupeKey: 'https://platform.moonshot.cn/docs',
        displayTitle: 'platform.moonshot.cn / docs',
        title: 'Moonshot platform docs',
        url: 'https://platform.moonshot.cn/docs',
        hostname: 'platform.moonshot.cn',
        trustLabel: 'Public web source',
      }),
    ),
    sseEvent(
      'source',
      envelope('source', {
        sourceId: 'source-3',
        dedupeKey: 'https://www.moonshot.cn/news',
        displayTitle: 'www.moonshot.cn / news',
        title: 'Moonshot public news',
        url: 'https://www.moonshot.cn/news',
        hostname: 'www.moonshot.cn',
        trustLabel: 'Public web source',
      }),
    ),
    sseEvent(
      'source',
      envelope('source', {
        sourceId: 'source-4',
        dedupeKey: 'https://www.moonshot.cn/about',
        displayTitle: 'www.moonshot.cn / about',
        title: 'Moonshot about',
        url: 'https://www.moonshot.cn/about',
        hostname: 'www.moonshot.cn',
        trustLabel: 'Public web source',
      }),
    ),
    sseEvent(
      'citation',
      envelope('citation', {
        citationId: 'cite-1',
        marker: '[ref_1]',
        title: 'Moonshot platform docs',
        url: 'https://platform.moonshot.cn/docs',
        sourceId: 'source-2',
        sourceIndex: 2,
      }),
    ),
    sseEvent('answer_delta', envelope('answer_delta', { content: answerText })),
    sseEvent('usage', envelope('usage', { output_chars: 25, source_count: 4, tool_count: 1, elapsed_ms: 320 })),
    sseEvent('done', envelope('done', { conversationId: 'c1' })),
  ].join('')

const server = http.createServer((request, response) => {
  if (request.method === 'OPTIONS') {
    response.writeHead(204, corsHeaders)
    response.end()
    return
  }

  if (request.url === '/api/v1/auth/login' && request.method === 'POST') {
    json(response, 200, {
      access_token: 'mock-student-token',
      token_type: 'bearer',
      provider: 'local-demo',
      issued_at: '2026-06-02T10:00:00Z',
      user: {
        id: 'student-1',
        displayName: '学生 Demo',
        role: 'student',
        demoAccount: true,
        sessionState: 'authenticated',
      },
    })
    return
  }

  if (request.url === '/api/v1/student/conversations' && request.method === 'GET') {
    json(response, 200, conversations())
    return
  }

  if (request.url === '/api/v1/student/chat/stream' && request.method === 'POST') {
    streamAttempts += 1
    if (streamAttempts === 1) {
      json(response, 401, { detail: 'Token expired in smoke.' })
      return
    }
    conversationReady = true
    response.writeHead(200, {
      ...corsHeaders,
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    })
    response.end(streamBody())
    return
  }

  json(response, 404, { detail: 'Not found' })
})

server.listen(port, '127.0.0.1', () => {
  console.log(`chatbox b-next mock api listening on http://127.0.0.1:${port}`)
})
