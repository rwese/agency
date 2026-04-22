import { Context, Next } from 'hono'
import { getAuthContext, extractTokenFromHeader } from '../lib/auth'

export interface AuthUser {
  userId: string
  username: string
  role: string
}

export interface AuthState {
  user: AuthUser | null
  isAuthenticated: boolean
  isAdmin: boolean
}

export interface Variables {
  auth: AuthState
}

export function authMiddleware() {
  return async (c: Context, next: Next) => {
    const authHeader = c.req.header('Authorization')
    const token = extractTokenFromHeader(authHeader)
    const ctx = await getAuthContext(token)

    c.set('auth', {
      user: ctx.user
        ? { userId: ctx.user.userId, username: ctx.user.username, role: ctx.user.role }
        : null,
      isAuthenticated: ctx.isAuthenticated,
      isAdmin: ctx.isAdmin,
    })

    await next()
  }
}

export function requireAuth() {
  return async (c: Context, next: Next) => {
    const auth = c.get('auth')
    if (!auth.isAuthenticated) {
      return c.json(
        {
          data: null,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Authentication required',
          },
        },
        401
      )
    }
    await next()
  }
}

export function requireAdmin() {
  return async (c: Context, next: Next) => {
    const auth = c.get('auth')
    if (!auth.isAuthenticated) {
      return c.json(
        {
          data: null,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Authentication required',
          },
        },
        401
      )
    }
    if (!auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Admin access required',
          },
        },
        403
      )
    }
    await next()
  }
}
