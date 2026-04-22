import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, type Variables } from '../middleware/auth'

const search = new Hono<{ Variables: Variables }>()

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

// GET /api/search - Full-text search across epics, tasks, and comments
search.get('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const q = c.req.query('q')
    const type = c.req.query('type') // 'epic', 'task', 'comment', or comma-separated
    const status = c.req.query('status')
    const priority = c.req.query('priority')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = Math.min(parseInt(c.req.query('per_page') || '20'), 100)

    if (!q || q.trim().length === 0) {
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

    // Get user's team IDs for scoping
    const userTeams = await prisma.userTeam.findMany({
      where: { userId: auth.user!.userId },
      select: { teamId: true },
    })
    const teamIds = userTeams.map((ut) => ut.teamId)

    // Determine which types to search
    const searchTypes = type
      ? type.split(',').map((t) => t.trim().toLowerCase())
      : ['epic', 'task', 'comment']

    const results: {
      epics: any[]
      tasks: any[]
      comments: any[]
    } = {
      epics: [],
      tasks: [],
      comments: [],
    }

    // Search epics if requested
    if (searchTypes.includes('epic')) {
      const epicWhere: any = {
        teamId: { in: teamIds },
        OR: [
          { title: { contains: q, mode: 'insensitive' } },
          { description: { contains: q, mode: 'insensitive' } },
        ],
      }

      if (status) {
        epicWhere.status = status
      }

      const epics = await prisma.epic.findMany({
        where: epicWhere,
        take,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          team: { select: { id: true, name: true } },
          createdBy: { select: { id: true, username: true } },
          _count: { select: { tasks: true } },
        },
      })

      results.epics = epics.map((epic) => ({
        type: 'epic',
        id: epic.id,
        title: epic.title,
        description: epic.description,
        status: epic.status,
        tags: parseTags(epic.tags),
        team: epic.team,
        task_count: epic._count.tasks,
        created_at: epic.createdAt.toISOString(),
        created_by: epic.createdBy,
      }))
    }

    // Search tasks if requested
    if (searchTypes.includes('task')) {
      const taskWhere: any = {
        epic: { teamId: { in: teamIds } },
        OR: [
          { title: { contains: q, mode: 'insensitive' } },
          { description: { contains: q, mode: 'insensitive' } },
        ],
      }

      if (status) {
        taskWhere.status = status
      }
      if (priority) {
        taskWhere.priority = priority
      }

      const tasks = await prisma.task.findMany({
        where: taskWhere,
        take,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          epic: { select: { id: true, title: true } },
          assignee: { select: { id: true, username: true } },
          createdBy: { select: { id: true, username: true } },
        },
      })

      results.tasks = tasks.map((task) => ({
        type: 'task',
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        tags: parseTags(task.tags),
        epic: task.epic,
        assignee: task.assignee,
        external_id: task.externalId,
        created_at: task.createdAt.toISOString(),
        created_by: task.createdBy,
      }))
    }

    // Search comments if requested
    if (searchTypes.includes('comment')) {
      // Get task IDs that user has access to
      const accessibleTasks = await prisma.task.findMany({
        where: {
          epic: { teamId: { in: teamIds } },
        },
        select: { id: true },
      })
      const taskIds = accessibleTasks.map((t) => t.id)

      const commentWhere: any = {
        taskId: { in: taskIds },
        content: { contains: q, mode: 'insensitive' },
      }

      const comments = await prisma.comment.findMany({
        where: commentWhere,
        take,
        skip,
        orderBy: { createdAt: 'desc' },
        include: {
          author: { select: { id: true, username: true } },
          task: {
            select: {
              id: true,
              title: true,
              epic: { select: { id: true, title: true } },
            },
          },
        },
      })

      results.comments = comments.map((comment) => ({
        type: 'comment',
        id: comment.id,
        content: comment.content,
        created_at: comment.createdAt.toISOString(),
        author: comment.author,
        task: {
          id: comment.task.id,
          title: comment.task.title,
          epic: comment.task.epic,
        },
      }))
    }

    // Combine and sort results by relevance (simple implementation: exact matches first)
    const combinedResults = [
      ...results.epics,
      ...results.tasks,
      ...results.comments,
    ].sort((a, b) => {
      // Simple relevance: prioritize exact title matches
      const aExact = a.title?.toLowerCase().includes(q.toLowerCase()) ? 1 : 0
      const bExact = b.title?.toLowerCase().includes(q.toLowerCase()) ? 1 : 0
      return bExact - aExact
    })

    return c.json({
      data: {
        results: combinedResults,
        breakdown: {
          epics: results.epics.length,
          tasks: results.tasks.length,
          comments: results.comments.length,
          total: combinedResults.length,
        },
      },
      meta: {
        page,
        per_page: perPage,
        query: q,
        types: searchTypes,
      },
    })
  } catch (error) {
    console.error('Search error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to search',
        },
      },
      500
    )
  }
})

export default search
