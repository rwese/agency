import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import {
  createToken,
  hashPassword,
  verifyPassword,
  generateApiKey,
} from '../lib/auth'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'
import { UserRole } from '@prisma/client'

const auth = new Hono<{ Variables: Variables }>()

// POST /auth/login
auth.post('/login', async (c) => {
  try {
    const { username, password } = await c.req.json()

    if (!username || !password) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Username and password are required',
          },
        },
        400
      )
    }

    const user = await prisma.user.findUnique({
      where: { username },
      include: {
        teams: {
          include: {
            team: {
              select: { id: true, name: true },
            },
          },
        },
      },
    })

    if (!user || !user.passwordHash) {
      return c.json(
        {
          data: null,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Invalid credentials',
          },
        },
        401
      )
    }

    const isValid = await verifyPassword(password, user.passwordHash)
    if (!isValid) {
      return c.json(
        {
          data: null,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Invalid credentials',
          },
        },
        401
      )
    }

    const token = await createToken({
      userId: user.id,
      username: user.username,
      role: user.role,
      email: user.email,
    })

    return c.json({
      data: {
        user: {
          id: user.id,
          username: user.username,
          role: user.role,
        },
        token,
      },
    })
  } catch (error) {
    console.error('Login error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Login failed',
        },
      },
      500
    )
  }
})

// POST /auth/logout
auth.post('/logout', requireAuth(), async (c) => {
  // For JWT-based auth, logout is typically handled client-side
  // by discarding the token. Server-side token blacklisting can be
  // implemented if needed for stricter security.
  return c.json({
    data: { success: true },
  })
})

// GET /auth/me
auth.get('/me', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    if (!auth.user) {
      return c.json(
        {
          data: null,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Not authenticated',
          },
        },
        401
      )
    }

    const user = await prisma.user.findUnique({
      where: { id: auth.user.userId },
      include: {
        teams: {
          include: {
            team: {
              select: { id: true, name: true },
            },
          },
        },
      },
    })

    if (!user) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'User not found',
          },
        },
        404
      )
    }

    return c.json({
      data: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        teams: user.teams.map((ut) => ut.team),
        createdAt: user.createdAt.toISOString(),
      },
    })
  } catch (error) {
    console.error('Get me error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get user info',
        },
      },
      500
    )
  }
})

// POST /auth/apikey - Generate API key (Admin only)
auth.post('/apikey', requireAdmin(), async (c) => {
  try {
    const { username, email, name, teamIds } = await c.req.json()

    if (!username || !email) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Username and email are required',
          },
        },
        400
      )
    }

    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [{ username }, { email }],
      },
    })

    if (existingUser) {
      return c.json(
        {
          data: null,
          error: {
            code: 'CONFLICT',
            message: 'Username or email already exists',
          },
        },
        409
      )
    }

    const { key, hash } = generateApiKey()

    // Create automation user
    const user = await prisma.user.create({
      data: {
        username,
        email,
        role: UserRole.automation,
        apiKeyHash: hash,
      },
    })

    // Add to teams if specified
    if (teamIds && Array.isArray(teamIds) && teamIds.length > 0) {
      await prisma.userTeam.createMany({
        data: teamIds.map((teamId: string) => ({
          userId: user.id,
          teamId,
          role: 'member',
        })),
      })
    }

    return c.json(
      {
        data: {
          api_key: key,
          user_id: user.id,
          name: name || username,
          created_at: new Date().toISOString(),
        },
      },
      201
    )
  } catch (error) {
    console.error('Create API key error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create API key',
        },
      },
      500
    )
  }
})

// POST /auth/register - Register new user (Admin only or for self-registration)
auth.post('/register', async (c) => {
  try {
    // This endpoint can be restricted based on your needs
    const { username, email, password, role, teamIds } = await c.req.json()

    if (!username || !email || !password) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Username, email, and password are required',
          },
        },
        400
      )
    }

    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [{ username }, { email }],
      },
    })

    if (existingUser) {
      return c.json(
        {
          data: null,
          error: {
            code: 'CONFLICT',
            message: 'Username or email already exists',
          },
        },
        409
      )
    }

    const passwordHash = await hashPassword(password)

    const user = await prisma.user.create({
      data: {
        username,
        email,
        passwordHash,
        role: role || UserRole.member,
      },
      include: {
        teams: {
          include: {
            team: {
              select: { id: true, name: true },
            },
          },
        },
      },
    })

    // Add to teams if specified
    if (teamIds && Array.isArray(teamIds) && teamIds.length > 0) {
      await prisma.userTeam.createMany({
        data: teamIds.map((teamId: string) => ({
          userId: user.id,
          teamId,
          role: 'member',
        })),
      })
    }

    return c.json(
      {
        data: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role,
          teams: user.teams.map((ut) => ut.team),
          createdAt: user.createdAt.toISOString(),
        },
      },
      201
    )
  } catch (error) {
    console.error('Register error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Registration failed',
        },
      },
      500
    )
  }
})

export default auth
