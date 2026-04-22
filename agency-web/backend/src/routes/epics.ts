import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'
import { dispatchWebhook } from '../lib/webhook'

const epics = new Hono<{ Variables: Variables }>()

// Helper for pagination
function getPagination(page: number, perPage: number) {
  const take = Math.min(perPage, 100)
  const skip = (page - 1) * take
  return { take, skip }
}

// Helper to parse tags from JSON string
function parseTags(tagsJson: string | null): string[] {
  if (!tagsJson) return []
  try {
    return JSON.parse(tagsJson)
  } catch {
    return []
  }
}

// Helper to serialize tags to JSON string
function serializeTags(tags: string[] | undefined): string | undefined {
  if (!tags || tags.length === 0) return undefined
  return JSON.stringify(tags)
}

// GET /epics - List epics (team-scoped for current user)
epics.get('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '20')
    const status = c.req.query('status')
    const teamId = c.req.query('team_id')
    const tag = c.req.query('tag')
    const createdBy = c.req.query('created_by')

    const { take, skip } = getPagination(page, perPage)

    // Get user's team IDs for scoping
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    const where: any = {
      teamId: { in: teamIds },
    }

    if (status) {
      where.status = status
    }
    if (teamId) {
      if (!teamIds.includes(teamId)) {
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
      where.teamId = teamId
    }
    if (createdBy) {
      where.createdById = createdBy
    }

    const [epics, total] = await Promise.all([
      prisma.epic.findMany({
        where,
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          team: {
            select: { id: true, name: true },
          },
          createdBy: {
            select: { id: true, username: true },
          },
          _count: {
            select: { tasks: true },
          },
        },
      }),
      prisma.epic.count({ where }),
    ])

    // Filter by tag if specified
    let result = epics
    if (tag) {
      result = epics.filter((epic) => {
        const tags = parseTags(epic.tags)
        return tags.includes(tag)
      })
    }

    return c.json({
      data: result.map((epic) => ({
        id: epic.id,
        title: epic.title,
        description: epic.description,
        status: epic.status,
        tags: parseTags(epic.tags),
        team: epic.team,
        task_count: epic._count.tasks,
        completed_task_count: 0, // Will be calculated separately if needed
        created_at: epic.createdAt.toISOString(),
        updated_at: epic.updatedAt.toISOString(),
        created_by: epic.createdBy,
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('List epics error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list epics',
        },
      },
      500
    )
  }
})

// POST /epics - Create new epic
epics.post('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const { title, description, status, tags, team_id } = await c.req.json()

    if (!title) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Title is required',
          },
        },
        400
      )
    }

    if (!team_id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'team_id is required',
          },
        },
        400
      )
    }

    // Check if user is a member of the team
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: team_id,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
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

    const epic = await prisma.epic.create({
      data: {
        title,
        description,
        status: status || 'open',
        tags: serializeTags(tags),
        teamId: team_id,
        createdById: auth.user!.userId,
      },
      include: {
        team: {
          select: { id: true, name: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    // Dispatch webhook for epic creation
    dispatchWebhook('epic.created', {
      epic_id: epic.id,
      title: epic.title,
      status: epic.status,
      team_id: epic.team.id,
      created_by: epic.createdBy.id,
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    return c.json(
      {
        data: {
          id: epic.id,
          title: epic.title,
          description: epic.description,
          status: epic.status,
          tags: parseTags(epic.tags),
          team: epic.team,
          created_at: epic.createdAt.toISOString(),
          updated_at: epic.updatedAt.toISOString(),
          created_by: epic.createdBy,
        },
      },
      201
    )
  } catch (error) {
    console.error('Create epic error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create epic',
        },
      },
      500
    )
  }
})

// GET /epics/search - Full-text search across epics
epics.get('/search', requireAuth(), async (c) => {
  try {
    const q = c.req.query('q')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '20')

    if (!q) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Search query (q) is required',
          },
        },
        400
      )
    }

    const { take, skip } = getPagination(page, perPage)
    const auth = c.get('auth')

    // Get user's team IDs
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    const [epics, total] = await Promise.all([
      prisma.epic.findMany({
        where: {
          teamId: { in: teamIds },
          OR: [
            { title: { contains: q, mode: 'insensitive' } },
            { description: { contains: q, mode: 'insensitive' } },
          ],
        },
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          team: {
            select: { id: true, name: true },
          },
          createdBy: {
            select: { id: true, username: true },
          },
        },
      }),
      prisma.epic.count({
        where: {
          teamId: { in: teamIds },
          OR: [
            { title: { contains: q, mode: 'insensitive' } },
            { description: { contains: q, mode: 'insensitive' } },
          ],
        },
      }),
    ])

    return c.json({
      data: epics.map((epic) => ({
        id: epic.id,
        title: epic.title,
        description: epic.description,
        status: epic.status,
        tags: parseTags(epic.tags),
        team: epic.team,
        created_at: epic.createdAt.toISOString(),
        updated_at: epic.updatedAt.toISOString(),
        created_by: epic.createdBy,
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('Search epics error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to search epics',
        },
      },
      500
    )
  }
})

// GET /epics/:id - Get epic with tasks
epics.get('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    const epic = await prisma.epic.findUnique({
      where: { id },
      include: {
        team: {
          select: { id: true, name: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
        tasks: {
          include: {
            assignee: {
              select: { id: true, username: true },
            },
            createdBy: {
              select: { id: true, username: true },
            },
          },
          orderBy: { createdAt: 'desc' },
        },
      },
    })

    if (!epic) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Epic not found',
          },
        },
        404
      )
    }

    // Check if user has access to this epic's team
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: epic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not a member of this epic\'s team',
          },
        },
        403
      )
    }

    return c.json({
      data: {
        id: epic.id,
        title: epic.title,
        description: epic.description,
        status: epic.status,
        tags: parseTags(epic.tags),
        team: epic.team,
        created_at: epic.createdAt.toISOString(),
        updated_at: epic.updatedAt.toISOString(),
        created_by: epic.createdBy,
        tasks: epic.tasks.map((task) => ({
          id: task.id,
          title: task.title,
          status: task.status,
          priority: task.priority,
          tags: parseTags(task.tags),
          assignee: task.assignee,
          external_id: task.externalId,
        })),
      },
    })
  } catch (error) {
    console.error('Get epic error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get epic',
        },
      },
      500
    )
  }
})

// PUT /epics/:id - Update epic
epics.put('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const { title, description, status, tags } = await c.req.json()
    const auth = c.get('auth')

    // Check if epic exists
    const existingEpic = await prisma.epic.findUnique({
      where: { id },
    })

    if (!existingEpic) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Epic not found',
          },
        },
        404
      )
    }

    // Check if user has access to this epic's team
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: existingEpic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to update this epic',
          },
        },
        403
      )
    }

    const updateData: any = {}
    if (title !== undefined) updateData.title = title
    if (description !== undefined) updateData.description = description
    if (status !== undefined) updateData.status = status
    if (tags !== undefined) updateData.tags = serializeTags(tags)

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

    const epic = await prisma.epic.update({
      where: { id },
      data: updateData,
      include: {
        team: {
          select: { id: true, name: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    // Dispatch webhooks for specific events
    const webhookPromises: Promise<void>[] = []

    // Status change event
    if (updateData.status && updateData.status !== existingEpic.status) {
      webhookPromises.push(
        dispatchWebhook('epic.status_changed', {
          epic_id: epic.id,
          title: epic.title,
          before: { status: existingEpic.status },
          after: { status: epic.status },
        })
      )
    }

    // General epic updated event
    webhookPromises.push(
      dispatchWebhook('epic.updated', {
        epic_id: epic.id,
        title: epic.title,
        changes: Object.keys(updateData),
      })
    )

    // Fire all webhooks (non-blocking)
    Promise.all(webhookPromises).catch((err) => console.error('Failed to dispatch webhooks:', err))

    return c.json({
      data: {
        id: epic.id,
        title: epic.title,
        description: epic.description,
        status: epic.status,
        tags: parseTags(epic.tags),
        team: epic.team,
        created_at: epic.createdAt.toISOString(),
        updated_at: epic.updatedAt.toISOString(),
        created_by: epic.createdBy,
      },
    })
  } catch (error) {
    console.error('Update epic error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update epic',
        },
      },
      500
    )
  }
})

// DELETE /epics/:id - Delete epic (Admin only)
epics.delete('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    // Check if epic exists
    const epic = await prisma.epic.findUnique({
      where: { id },
    })

    if (!epic) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Epic not found',
          },
        },
        404
      )
    }

    // Dispatch webhook for epic deletion
    dispatchWebhook('epic.deleted', {
      epic_id: id,
      title: epic.title,
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    // Delete epic (cascades to tasks)
    await prisma.epic.delete({
      where: { id },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete epic error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete epic',
        },
      },
      500
    )
  }
})

export default epics
