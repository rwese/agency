import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAdmin, type Variables } from '../middleware/auth'

const admin = new Hono<{ Variables: Variables }>()

// GET /admin/metrics - Get usage metrics
admin.get('/metrics', requireAdmin(), async (c) => {
  try {
    const now = new Date()
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

    // Get counts
    const [
      totalUsers,
      totalTeams,
      totalEpics,
      totalTasks,
      totalAttachments,
      totalComments,
      totalWebhooks,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.team.count(),
      prisma.epic.count(),
      prisma.task.count(),
      prisma.attachment.count(),
      prisma.comment.count(),
      prisma.webhook.count(),
    ])

    // Get active users in last 7 days (users who performed any action)
    const activeUsers7d = await prisma.activityLog.findMany({
      where: {
        createdAt: { gte: sevenDaysAgo },
        actorId: { not: null },
      },
      select: { actorId: true },
      distinct: ['actorId'],
    })

    // Get tasks created in last 7 days
    const tasksCreated7d = await prisma.task.count({
      where: {
        createdAt: { gte: sevenDaysAgo },
      },
    })

    // Get tasks completed in last 7 days
    const tasksCompleted7d = await prisma.task.count({
      where: {
        status: 'done',
        updatedAt: { gte: sevenDaysAgo },
      },
    })

    // Get task stats by status
    const taskStatsByStatus = await prisma.task.groupBy({
      by: ['status'],
      _count: { status: true },
    })

    // Get task stats by priority
    const taskStatsByPriority = await prisma.task.groupBy({
      by: ['priority'],
      _count: { priority: true },
    })

    // Get epic stats by status
    const epicStatsByStatus = await prisma.epic.groupBy({
      by: ['status'],
      _count: { status: true },
    })

    // Get user stats by role
    const userStatsByRole = await prisma.user.groupBy({
      by: ['role'],
      _count: { role: true },
    })

    return c.json({
      data: {
        totals: {
          users: totalUsers,
          teams: totalTeams,
          epics: totalEpics,
          tasks: totalTasks,
          attachments: totalAttachments,
          comments: totalComments,
          webhooks: totalWebhooks,
        },
        activity_7d: {
          active_users: activeUsers7d.length,
          tasks_created: tasksCreated7d,
          tasks_completed: tasksCompleted7d,
        },
        task_stats: {
          by_status: taskStatsByStatus.reduce((acc, stat) => {
            acc[stat.status] = stat._count.status
            return acc
          }, {} as Record<string, number>),
          by_priority: taskStatsByPriority.reduce((acc, stat) => {
            acc[stat.priority] = stat._count.priority
            return acc
          }, {} as Record<string, number>),
        },
        epic_stats: {
          by_status: epicStatsByStatus.reduce((acc, stat) => {
            acc[stat.status] = stat._count.status
            return acc
          }, {} as Record<string, number>),
        },
        user_stats: {
          by_role: userStatsByRole.reduce((acc, stat) => {
            acc[stat.role] = stat._count.role
            return acc
          }, {} as Record<string, number>),
        },
      },
    })
  } catch (error) {
    console.error('Get metrics error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get metrics',
        },
      },
      500
    )
  }
})

// GET /admin/activity - Get activity logs
admin.get('/activity', requireAdmin(), async (c) => {
  try {
    const page = parseInt(c.req.query('page') || '1')
    const perPage = Math.min(parseInt(c.req.query('per_page') || '50'), 100)
    const entityType = c.req.query('entity_type')
    const actorId = c.req.query('actor_id')
    const action = c.req.query('action')

    const skip = (page - 1) * perPage

    // Build where clause
    const where: any = {}
    if (entityType) where.entityType = entityType
    if (actorId) where.actorId = actorId
    if (action) where.action = action

    const [logs, total] = await Promise.all([
      prisma.activityLog.findMany({
        where,
        skip,
        take: perPage,
        orderBy: { createdAt: 'desc' },
        include: {
          actor: {
            select: { id: true, username: true },
          },
        },
      }),
      prisma.activityLog.count({ where }),
    ])

    return c.json({
      data: logs.map((log) => ({
        id: log.id,
        action: log.action,
        entity_type: log.entityType,
        entity_id: log.entityId,
        actor: log.actor,
        payload: log.payload ? JSON.parse(log.payload) : null,
        created_at: log.createdAt.toISOString(),
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('Get activity logs error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get activity logs',
        },
      },
      500
    )
  }
})

// POST /admin/activity - Create manual activity log entry
admin.post('/activity', requireAdmin(), async (c) => {
  try {
    const { action, entity_type, entity_id, payload } = await c.req.json()
    const auth = c.get('auth')

    if (!action || !entity_type || !entity_id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'action, entity_type, and entity_id are required',
          },
        },
        400
      )
    }

    const log = await prisma.activityLog.create({
      data: {
        action,
        entityType: entity_type,
        entityId: entity_id,
        actorId: auth.user!.userId,
        payload: payload ? JSON.stringify(payload) : null,
      },
      include: {
        actor: {
          select: { id: true, username: true },
        },
      },
    })

    return c.json(
      {
        data: {
          id: log.id,
          action: log.action,
          entity_type: log.entityType,
          entity_id: log.entityId,
          actor: log.actor,
          payload: log.payload ? JSON.parse(log.payload) : null,
          created_at: log.createdAt.toISOString(),
        },
      },
      201
    )
  } catch (error) {
    console.error('Create activity log error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create activity log',
        },
      },
      500
    )
  }
})

export default admin
