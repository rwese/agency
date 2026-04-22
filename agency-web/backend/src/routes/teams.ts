import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'

const teams = new Hono<{ Variables: Variables }>()

// Helper for pagination
function getPagination(page: number, perPage: number) {
  const take = Math.min(perPage, 100)
  const skip = (page - 1) * take
  return { take, skip }
}

// GET /teams - List teams current user belongs to
teams.get('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '20')

    const { take, skip } = getPagination(page, perPage)

    // Get user's team IDs
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    const [teams, total] = await Promise.all([
      prisma.team.findMany({
        where: {
          id: { in: teamIds },
        },
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          _count: {
            select: { members: true },
          },
        },
      }),
      prisma.team.count({
        where: { id: { in: teamIds } },
      }),
    ])

    return c.json({
      data: teams.map((team) => ({
        id: team.id,
        name: team.name,
        description: team.description,
        member_count: team._count.members,
        created_at: team.createdAt.toISOString(),
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('List teams error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list teams',
        },
      },
      500
    )
  }
})

// POST /teams - Create new team (Admin only)
teams.post('/', requireAdmin(), async (c) => {
  try {
    const { name, description } = await c.req.json()

    if (!name) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Team name is required',
          },
        },
        400
      )
    }

    // Check if team already exists
    const existingTeam = await prisma.team.findUnique({
      where: { name },
    })

    if (existingTeam) {
      return c.json(
        {
          data: null,
          error: {
            code: 'CONFLICT',
            message: 'Team with this name already exists',
          },
        },
        409
      )
    }

    const team = await prisma.team.create({
      data: {
        name,
        description,
      },
    })

    return c.json(
      {
        data: {
          id: team.id,
          name: team.name,
          description: team.description,
          created_at: team.createdAt.toISOString(),
        },
      },
      201
    )
  } catch (error) {
    console.error('Create team error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create team',
        },
      },
      500
    )
  }
})

// GET /teams/:id - Get team details with members
teams.get('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    const team = await prisma.team.findUnique({
      where: { id },
      include: {
        members: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                role: true,
              },
            },
          },
        },
      },
    })

    if (!team) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Team not found',
          },
        },
        404
      )
    }

    // Check if user is a member or admin
    const isMember = team.members.some((m) => m.userId === auth.user!.userId)
    if (!isMember && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not a member of this team',
          },
        },
        403
      )
    }

    return c.json({
      data: {
        id: team.id,
        name: team.name,
        description: team.description,
        members: team.members.map((m) => ({
          id: m.user.id,
          username: m.user.username,
          role: m.role,
        })),
        created_at: team.createdAt.toISOString(),
      },
    })
  } catch (error) {
    console.error('Get team error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get team',
        },
      },
      500
    )
  }
})

// PUT /teams/:id - Update team
teams.put('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const { name, description } = await c.req.json()
    const auth = c.get('auth')

    // Check if team exists
    const existingTeam = await prisma.team.findUnique({
      where: { id },
    })

    if (!existingTeam) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Team not found',
          },
        },
        404
      )
    }

    // Check if user is a member or admin
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: id,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to update this team',
          },
        },
        403
      )
    }

    const updateData: any = {}
    if (name !== undefined) {
      updateData.name = name
    }
    if (description !== undefined) {
      updateData.description = description
    }

    if (Object.keys(updateData).length === 0) {
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

    // Check for duplicate name
    if (name) {
      const duplicateTeam = await prisma.team.findFirst({
        where: {
          name,
          NOT: { id },
        },
      })

      if (duplicateTeam) {
        return c.json(
          {
            data: null,
            error: {
              code: 'CONFLICT',
              message: 'Team with this name already exists',
            },
          },
          409
        )
      }
    }

    const team = await prisma.team.update({
      where: { id },
      data: updateData,
      include: {
        members: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                role: true,
              },
            },
          },
        },
      },
    })

    return c.json({
      data: {
        id: team.id,
        name: team.name,
        description: team.description,
        members: team.members.map((m) => ({
          id: m.user.id,
          username: m.user.username,
          role: m.role,
        })),
        created_at: team.createdAt.toISOString(),
      },
    })
  } catch (error) {
    console.error('Update team error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update team',
        },
      },
      500
    )
  }
})

// DELETE /teams/:id - Delete team (Admin only)
teams.delete('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    // Check if team exists
    const team = await prisma.team.findUnique({
      where: { id },
    })

    if (!team) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Team not found',
          },
        },
        404
      )
    }

    await prisma.team.delete({
      where: { id },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete team error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete team',
        },
      },
      500
    )
  }
})

// POST /teams/:id/members - Add member to team
teams.post('/:id/members', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const { user_id } = await c.req.json()
    const auth = c.get('auth')

    // Check if team exists
    const team = await prisma.team.findUnique({
      where: { id },
    })

    if (!team) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Team not found',
          },
        },
        404
      )
    }

    // Check if user is a member/admin (to add others) or admin
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: id,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to add members to this team',
          },
        },
        403
      )
    }

    if (!user_id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'user_id is required',
          },
        },
        400
      )
    }

    // Check if user exists
    const user = await prisma.user.findUnique({
      where: { id: user_id },
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

    // Check if already a member
    const existingMember = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: user_id,
          teamId: id,
        },
      },
    })

    if (existingMember) {
      return c.json(
        {
          data: null,
          error: {
            code: 'CONFLICT',
            message: 'User is already a member of this team',
          },
        },
        409
      )
    }

    await prisma.userTeam.create({
      data: {
        userId: user_id,
        teamId: id,
        role: 'member',
      },
    })

    return c.json(
      {
        data: { success: true },
      },
      201
    )
  } catch (error) {
    console.error('Add team member error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to add team member',
        },
      },
      500
    )
  }
})

// DELETE /teams/:id/members/:userId - Remove member from team
teams.delete('/:id/members/:userId', requireAuth(), async (c) => {
  try {
    const { id, userId } = c.req.param()
    const auth = c.get('auth')

    // Check if team exists
    const team = await prisma.team.findUnique({
      where: { id },
    })

    if (!team) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Team not found',
          },
        },
        404
      )
    }

    // Check if user is a member/admin (to remove others) or admin
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: id,
        },
      },
    })

    // Can remove if: admin, removing self, or user is member of the team
    const canRemove = auth.isAdmin || auth.user!.userId === userId || userTeam

    if (!canRemove) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to remove members from this team',
          },
        },
        403
      )
    }

    // Check if member exists
    const member = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId,
          teamId: id,
        },
      },
    })

    if (!member) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'User is not a member of this team',
          },
        },
        404
      )
    }

    await prisma.userTeam.delete({
      where: {
        userId_teamId: {
          userId,
          teamId: id,
        },
      },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Remove team member error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to remove team member',
        },
      },
      500
    )
  }
})

export default teams
