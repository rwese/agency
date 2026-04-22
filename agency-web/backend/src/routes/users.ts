import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { hashPassword } from '../lib/auth'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'
import { UserRole } from '@prisma/client'

const users = new Hono<{ Variables: Variables }>()

// Helper for pagination
function getPagination(page: number, perPage: number) {
  const take = Math.min(perPage, 100)
  const skip = (page - 1) * take
  return { take, skip }
}

// GET /users - List all users (Admin only)
users.get('/', requireAdmin(), async (c) => {
  try {
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '20')
    const role = c.req.query('role')
    const teamId = c.req.query('team_id')

    const { take, skip } = getPagination(page, perPage)

    const where: any = {}
    if (role) {
      where.role = role
    }
    if (teamId) {
      where.teams = {
        some: {
          teamId,
        },
      }
    }

    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          teams: {
            include: {
              team: {
                select: { id: true, name: true },
              },
            },
          },
        },
      }),
      prisma.user.count({ where }),
    ])

    return c.json({
      data: users.map((user) => ({
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        teams: user.teams.map((ut) => ut.team.name),
        createdAt: user.createdAt.toISOString(),
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('List users error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list users',
        },
      },
      500
    )
  }
})

// POST /users - Create new user (Admin only)
users.post('/', requireAdmin(), async (c) => {
  try {
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

    // Fetch updated user with teams
    const updatedUser = await prisma.user.findUnique({
      where: { id: user.id },
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

    return c.json(
      {
        data: {
          id: updatedUser!.id,
          username: updatedUser!.username,
          email: updatedUser!.email,
          role: updatedUser!.role,
          teams: updatedUser!.teams.map((ut) => ut.team),
          createdAt: updatedUser!.createdAt.toISOString(),
        },
      },
      201
    )
  } catch (error) {
    console.error('Create user error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create user',
        },
      },
      500
    )
  }
})

// GET /users/me - Get current user
users.get('/me', requireAuth(), async (c) => {
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
    console.error('Get user error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get user',
        },
      },
      500
    )
  }
})

// GET /users/:id - Get user by ID
users.get('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()

    const user = await prisma.user.findUnique({
      where: { id },
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
    console.error('Get user error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get user',
        },
      },
      500
    )
  }
})

// PUT /users/:id - Update user
users.put('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')
    const updates = await c.req.json()

    // Check permissions: admin can update anyone, regular users can only update themselves (limited fields)
    if (!auth.isAdmin && auth.user?.userId !== id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Cannot update other users',
          },
        },
        403
      )
    }

    // Non-admins can only update limited fields
    const allowedFields = auth.isAdmin
      ? ['email', 'role', 'teamIds']
      : ['email']

    const data: any = {}
    for (const field of allowedFields) {
      if (field in updates) {
        if (field === 'teamIds') {
          // Handle team membership changes
          const teamIds: string[] = updates[field]
          // Remove from all teams first
          await prisma.userTeam.deleteMany({
            where: { userId: id },
          })
          // Add to new teams
          if (teamIds.length > 0) {
            await prisma.userTeam.createMany({
              data: teamIds.map((teamId: string) => ({
                userId: id,
                teamId,
                role: 'member',
              })),
            })
          }
        } else {
          data[field] = updates[field]
        }
      }
    }

    if (Object.keys(data).length === 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'No valid fields to update',
          },
        },
        400
      )
    }

    const user = await prisma.user.update({
      where: { id },
      data,
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
    console.error('Update user error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update user',
        },
      },
      500
    )
  }
})

// DELETE /users/:id - Delete user (Admin only)
users.delete('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    // Check if user exists
    const user = await prisma.user.findUnique({
      where: { id },
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

    // Prevent deleting self
    const auth = c.get('auth')
    if (auth.user?.userId === id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Cannot delete yourself',
          },
        },
        403
      )
    }

    await prisma.user.delete({
      where: { id },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete user error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete user',
        },
      },
      500
    )
  }
})

export default users
