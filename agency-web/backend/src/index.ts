import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'

const app = new Hono()

app.use('*', cors())
app.use('*', logger())

app.get('/', (c) => c.json({ message: 'agency-web API', version: '1.0.0' }))

app.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }))

// Auth routes placeholder
app.post('/api/auth/login', async (c) => {
  const { email, password } = await c.req.json()
  // TODO: Implement auth
  return c.json({ token: 'demo-token', user: { id: '1', email } })
})

// Epic routes placeholder
app.get('/api/epics', (c) => c.json([]))
app.post('/api/epics', async (c) => {
  const body = await c.req.json()
  return c.json({ id: '1', ...body }, 201)
})

// Task routes placeholder
app.get('/api/tasks', (c) => c.json([]))
app.post('/api/tasks', async (c) => {
  const body = await c.req.json()
  return c.json({ id: '1', ...body }, 201)
})

const PORT = parseInt(process.env.PORT || '3000')
console.log(`Starting server on port ${PORT}`)

export default {
  port: PORT,
  fetch: app.fetch,
}
