import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'
import { dispatchWebhook } from '../lib/webhook'

const tasks = new Hono<{ Variables: Variables }>()

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

// GET /tasks - List tasks with filters
tasks.get('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '20')
    const status = c.req.query('status')
    const priority = c.req.query('priority')
    const epicId = c.req.query('epic_id')
    const teamId = c.req.query('team_id')
    const assigneeId = c.req.query('assignee_id')
    const tag = c.req.query('tag')
    const externalId = c.req.query('external_id')
    const createdBy = c.req.query('created_by')

    const { take, skip } = getPagination(page, perPage)

    // Get user's team IDs for scoping
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    // Build where clause
    const where: any = {
      epic: {
        teamId: { in: teamIds },
      },
    }

    if (status) where.status = status
    if (priority) where.priority = priority
    if (epicId) where.epicId = epicId
    if (assigneeId) where.assigneeId = assigneeId
    if (externalId) where.externalId = externalId
    if (createdBy) where.createdById = createdBy

    // Filter by team if specified
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
      where.epic = { ...where.epic, teamId }
    }

    const [taskList, total] = await Promise.all([
      prisma.task.findMany({
        where,
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          epic: {
            select: { id: true, title: true },
          },
          assignee: {
            select: { id: true, username: true },
          },
          createdBy: {
            select: { id: true, username: true },
          },
          _count: {
            select: { comments: true, attachments: true, githubRefs: true },
          },
        },
      }),
      prisma.task.count({ where }),
    ])

    // Filter by tag if specified (client-side due to JSON storage)
    let result = taskList
    if (tag) {
      result = taskList.filter((task) => parseTags(task.tags).includes(tag))
    }

    return c.json({
      data: result.map((task) => ({
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        tags: parseTags(task.tags),
        external_id: task.externalId,
        created_at: task.createdAt.toISOString(),
        updated_at: task.updatedAt.toISOString(),
        epic: task.epic,
        team: { id: '', name: '' }, // Will be populated via epic.team in the actual response
        assignee: task.assignee,
        created_by: task.createdBy,
        attachment_count: task._count.attachments,
        comment_count: task._count.comments,
        github_ref_count: task._count.githubRefs,
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('List tasks error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list tasks',
        },
      },
      500
    )
  }
})

// POST /tasks - Create new task
tasks.post('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const {
      title,
      description,
      status,
      priority,
      tags,
      external_id,
      epic_id,
      assignee_id,
    } = await c.req.json()

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

    if (!epic_id) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'epic_id is required',
          },
        },
        400
      )
    }

    // Check if epic exists and user has access to its team
    const epic = await prisma.epic.findUnique({
      where: { id: epic_id },
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

    const task = await prisma.task.create({
      data: {
        title,
        description,
        status: status || 'open',
        priority: priority || 'medium',
        tags: serializeTags(tags),
        externalId: external_id,
        epicId: epic_id,
        assigneeId: assignee_id,
        createdById: auth.user!.userId,
      },
      include: {
        epic: {
          select: { id: true, title: true },
        },
        assignee: {
          select: { id: true, username: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    // Dispatch webhook for task creation
    dispatchWebhook('task.created', {
      task_id: task.id,
      title: task.title,
      status: task.status,
      priority: task.priority,
      epic_id: task.epic.id,
      assignee_id: task.assigneeId,
      created_by: task.createdBy.id,
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    return c.json(
      {
        data: {
          id: task.id,
          title: task.title,
          description: task.description,
          status: task.status,
          priority: task.priority,
          tags: parseTags(task.tags),
          external_id: task.externalId,
          created_at: task.createdAt.toISOString(),
          updated_at: task.updatedAt.toISOString(),
          epic: task.epic,
          assignee: task.assignee,
          created_by: task.createdBy,
        },
      },
      201
    )
  } catch (error) {
    console.error('Create task error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create task',
        },
      },
      500
    )
  }
})

// GET /tasks/search - Full-text search across tasks
tasks.get('/search', requireAuth(), async (c) => {
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

    const [taskList, total] = await Promise.all([
      prisma.task.findMany({
        where: {
          epic: {
            teamId: { in: teamIds },
          },
          OR: [
            { title: { contains: q, mode: 'insensitive' } },
            { description: { contains: q, mode: 'insensitive' } },
          ],
        },
        skip,
        take,
        orderBy: { createdAt: 'desc' },
        include: {
          epic: {
            select: { id: true, title: true },
          },
          assignee: {
            select: { id: true, username: true },
          },
          createdBy: {
            select: { id: true, username: true },
          },
        },
      }),
      prisma.task.count({
        where: {
          epic: {
            teamId: { in: teamIds },
          },
          OR: [
            { title: { contains: q, mode: 'insensitive' } },
            { description: { contains: q, mode: 'insensitive' } },
          ],
        },
      }),
    ])

    return c.json({
      data: taskList.map((task) => ({
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        tags: parseTags(task.tags),
        external_id: task.externalId,
        created_at: task.createdAt.toISOString(),
        updated_at: task.updatedAt.toISOString(),
        epic: task.epic,
        assignee: task.assignee,
        created_by: task.createdBy,
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('Search tasks error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to search tasks',
        },
      },
      500
    )
  }
})

// GET /tasks/:id - Get task with comments, attachments, and GitHub refs
tasks.get('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    const task = await prisma.task.findUnique({
      where: { id },
      include: {
        epic: {
          select: { id: true, title: true },
        },
        assignee: {
          select: { id: true, username: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
        comments: {
          include: {
            author: {
              select: { id: true, username: true },
            },
          },
          orderBy: { createdAt: 'asc' },
        },
        attachments: {
          include: {
            uploadedBy: {
              select: { id: true, username: true },
            },
          },
          orderBy: { uploadedAt: 'desc' },
        },
        githubRefs: true,
      },
    })

    if (!task) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Task not found',
          },
        },
        404
      )
    }

    // Check if user has access to this task's team (via epic)
    const epic = await prisma.epic.findUnique({
      where: { id: task.epicId },
    })

    if (!epic) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Task epic not found',
          },
        },
        404
      )
    }

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
            message: 'Not authorized to view this task',
          },
        },
        403
      )
    }

    // Get team info
    const team = await prisma.team.findUnique({
      where: { id: epic.teamId },
      select: { id: true, name: true },
    })

    return c.json({
      data: {
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        tags: parseTags(task.tags),
        external_id: task.externalId,
        created_at: task.createdAt.toISOString(),
        updated_at: task.updatedAt.toISOString(),
        epic: task.epic,
        team: team,
        assignee: task.assignee,
        created_by: task.createdBy,
        comments: task.comments.map((comment) => ({
          id: comment.id,
          content: comment.content,
          created_at: comment.createdAt.toISOString(),
          updated_at: comment.updatedAt.toISOString(),
          author: comment.author,
        })),
        attachments: task.attachments.map((att) => ({
          id: att.id,
          filename: att.filename,
          content_type: att.contentType,
          size_bytes: att.sizeBytes,
          storage_path: att.storagePath,
          uploaded_at: att.uploadedAt.toISOString(),
          uploaded_by: att.uploadedBy,
        })),
        github_refs: task.githubRefs.map((ref) => ({
          id: ref.id,
          ref_type: ref.refType,
          ref_id: ref.refId,
          url: ref.url,
          created_at: ref.createdAt.toISOString(),
        })),
      },
    })
  } catch (error) {
    console.error('Get task error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get task',
        },
      },
      500
    )
  }
})

// PUT /tasks/:id - Update task
tasks.put('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const {
      title,
      description,
      status,
      priority,
      tags,
      external_id,
      assignee_id,
    } = await c.req.json()
    const auth = c.get('auth')

    // Check if task exists
    const existingTask = await prisma.task.findUnique({
      where: { id },
    })

    if (!existingTask) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Task not found',
          },
        },
        404
      )
    }

    // Check if user has access to this task's team (via epic)
    const epic = await prisma.epic.findUnique({
      where: { id: existingTask.epicId },
    })

    if (!epic) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Task epic not found',
          },
        },
        404
      )
    }

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
            message: 'Not authorized to update this task',
          },
        },
        403
      )
    }

    const updateData: any = {}
    if (title !== undefined) updateData.title = title
    if (description !== undefined) updateData.description = description
    if (status !== undefined) {
      updateData.status = status
      // Set completedAt if marking as done
      if (status === 'done' && existingTask.status !== 'done') {
        updateData.completedAt = new Date()
      }
    }
    if (priority !== undefined) updateData.priority = priority
    if (tags !== undefined) updateData.tags = serializeTags(tags)
    if (external_id !== undefined) updateData.externalId = external_id
    if (assignee_id !== undefined) updateData.assigneeId = assignee_id

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

    const task = await prisma.task.update({
      where: { id },
      data: updateData,
      include: {
        epic: {
          select: { id: true, title: true },
        },
        assignee: {
          select: { id: true, username: true },
        },
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    // Get team info
    const team = await prisma.team.findUnique({
      where: { id: epic.teamId },
      select: { id: true, name: true },
    })

    // Dispatch webhooks for specific events
    const webhookPromises: Promise<void>[] = []

    // Status change event
    if (updateData.status && updateData.status !== existingTask.status) {
      webhookPromises.push(
        dispatchWebhook('task.status_changed', {
          task_id: task.id,
          title: task.title,
          before: { status: existingTask.status },
          after: { status: task.status },
        })
      )
    }

    // Assignee change event
    if (assignee_id !== undefined && assignee_id !== existingTask.assigneeId) {
      webhookPromises.push(
        dispatchWebhook('task.assigned', {
          task_id: task.id,
          title: task.title,
          before: { assignee_id: existingTask.assigneeId },
          after: { assignee_id: assignee_id },
        })
      )
    }

    // Priority change event
    if (updateData.priority && updateData.priority !== existingTask.priority) {
      webhookPromises.push(
        dispatchWebhook('task.priority_changed', {
          task_id: task.id,
          title: task.title,
          before: { priority: existingTask.priority },
          after: { priority: task.priority },
        })
      )
    }

    // General task updated event
    webhookPromises.push(
      dispatchWebhook('task.updated', {
        task_id: task.id,
        title: task.title,
        changes: Object.keys(updateData),
      })
    )

    // Fire all webhooks (non-blocking)
    Promise.all(webhookPromises).catch((err) => console.error('Failed to dispatch webhooks:', err))

    return c.json({
      data: {
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        tags: parseTags(task.tags),
        external_id: task.externalId,
        created_at: task.createdAt.toISOString(),
        updated_at: task.updatedAt.toISOString(),
        epic: task.epic,
        team: team,
        assignee: task.assignee,
        created_by: task.createdBy,
      },
    })
  } catch (error) {
    console.error('Update task error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update task',
        },
      },
      500
    )
  }
})

// DELETE /tasks/:id - Delete task (Admin or creator)
tasks.delete('/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    // Check if task exists
    const task = await prisma.task.findUnique({
      where: { id },
    })

    if (!task) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Task not found',
          },
        },
        404
      )
    }

    // Check permissions: admin or creator
    if (!auth.isAdmin && task.createdById !== auth.user!.userId) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to delete this task',
          },
        },
        403
      )
    }

    await prisma.task.delete({
      where: { id },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete task error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete task',
        },
      },
      500
    )
  }
})

// POST /tasks/bulk - Bulk update task statuses
tasks.post('/bulk', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const { task_ids, status } = await c.req.json()

    if (!task_ids || !Array.isArray(task_ids) || task_ids.length === 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'task_ids array is required',
          },
        },
        400
      )
    }

    if (!status) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'status is required',
          },
        },
        400
      )
    }

    // Get tasks and their epics for access check
    const tasksToUpdate = await prisma.task.findMany({
      where: { id: { in: task_ids } },
      include: {
        epic: {
          select: { teamId: true },
        },
      },
    })

    if (tasksToUpdate.length !== task_ids.length) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'One or more tasks not found',
          },
        },
        404
      )
    }

    // Get user's team IDs
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    // Get all team IDs that tasks belong to
    const taskTeamIds = [...new Set(tasksToUpdate.map((t) => t.epic.teamId))]

    // Check user has access to all teams
    const hasAccess = taskTeamIds.every((tid) => teamIds.includes(tid))
    if (!hasAccess && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to update some tasks',
          },
        },
        403
      )
    }

    const updateData: any = { status }
    if (status === 'done') {
      updateData.completedAt = new Date()
    }

    const updateResult = await prisma.task.updateMany({
      where: {
        id: { in: task_ids },
        epic: {
          teamId: { in: teamIds },
        },
      },
      data: updateData,
    })

    return c.json({
      data: {
        updated_count: updateResult.count,
      },
    })
  } catch (error) {
    console.error('Bulk update tasks error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to bulk update tasks',
        },
      },
      500
    )
  }
})

export default tasks
