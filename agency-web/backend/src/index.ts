import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { authMiddleware } from './middleware/auth'
import authRoutes from './routes/auth'
import usersRoutes from './routes/users'
import teamsRoutes from './routes/teams'
import epicsRoutes from './routes/epics'
import tasksRoutes from './routes/tasks'
import commentsRoutes from './routes/comments'
import attachmentsRoutes from './routes/attachments'
import webhooksRoutes from './routes/webhooks'
import githubRoutes from './routes/github'
import searchRoutes from './routes/search'
import adminRoutes from './routes/admin'

const app = new Hono()

// Global middleware
app.use('*', cors())
app.use('*', logger())
app.use('*', authMiddleware())

// Health check
app.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }))

// Mount auth routes
app.route('/api/auth', authRoutes)

// Mount users routes (CRUD implemented)
app.route('/api/users', usersRoutes)

// Mount teams routes (CRUD implemented)
app.route('/api/teams', teamsRoutes)

// Mount epics routes (CRUD implemented)
app.route('/api/epics', epicsRoutes)

// Mount tasks routes (CRUD implemented)
app.route('/api/tasks', tasksRoutes)

// Mount comments routes
app.route('/api', commentsRoutes)

// Mount attachments routes
app.route('/api', attachmentsRoutes)

// Mount webhooks routes
app.route('/api/webhooks', webhooksRoutes)

// Mount GitHub integration routes
app.route('/api/github', githubRoutes)

// Mount search routes
app.route('/api', searchRoutes)

// Mount admin routes
app.route('/api/admin', adminRoutes)

const PORT = parseInt(process.env.PORT || '3000')
console.log(`Starting server on port ${PORT}`)

export default {
  port: PORT,
  fetch: app.fetch,
}
