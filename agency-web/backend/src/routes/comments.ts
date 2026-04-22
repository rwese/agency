import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, type Variables } from '../middleware/auth'
import { dispatchWebhook } from '../lib/webhook'

const comments = new Hono<{ Variables: Variables }>()

// Helper to extract @mentions from content
function extractMentions(content: string): string[] {
  const mentionRegex = /@(\w+)/g
  const mentions: string[] = []
  let match
  while ((match = mentionRegex.exec(content)) !== null) {
    mentions.push(match[1])
  }
  return [...new Set(mentions)] // Remove duplicates
}

// Helper to render markdown (basic implementation)
function renderMarkdown(content: string): string {
  // Basic markdown rendering - in production use a proper library like marked or remark
  let html = content
    // Escape HTML first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Code blocks
    .replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`(.+?)`/g, '<code>$1</code>')
    // Links
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Line breaks
    .replace(/\n/g, '<br>')
    // @mentions - make them clickable
    .replace(/@(\w+)/g, '<a href="/users/$1" class="mention">@$1</a>')
  return html
}

// GET /api/tasks/:taskId/comments - List comments for a task
comments.get('/tasks/:taskId/comments', requireAuth(), async (c) => {
  try {
    const { taskId } = c.req.param()
    const auth = c.get('auth')
    const page = parseInt(c.req.query('page') || '1')
    const perPage = parseInt(c.req.query('per_page') || '50')

    // Check if task exists
    const task = await prisma.task.findUnique({
      where: { id: taskId },
      include: {
        epic: {
          select: { teamId: true },
        },
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

    // Check access
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: task.epic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to view comments for this task',
          },
        },
        403
      )
    }

    const skip = (page - 1) * perPage

    const [commentList, total] = await Promise.all([
      prisma.comment.findMany({
        where: { taskId },
        skip,
        take: perPage,
        orderBy: { createdAt: 'asc' },
        include: {
          author: {
            select: { id: true, username: true },
          },
        },
      }),
      prisma.comment.count({ where: { taskId } }),
    ])

    return c.json({
      data: commentList.map((comment) => ({
        id: comment.id,
        content: comment.content,
        content_html: renderMarkdown(comment.content),
        mentions: extractMentions(comment.content),
        created_at: comment.createdAt.toISOString(),
        updated_at: comment.updatedAt.toISOString(),
        author: comment.author,
      })),
      meta: {
        page,
        per_page: perPage,
        total,
      },
    })
  } catch (error) {
    console.error('List comments error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list comments',
        },
      },
      500
    )
  }
})

// POST /api/tasks/:taskId/comments - Create a new comment
comments.post('/tasks/:taskId/comments', requireAuth(), async (c) => {
  try {
    const { taskId } = c.req.param()
    const { content } = await c.req.json()
    const auth = c.get('auth')

    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Content is required and must be a non-empty string',
          },
        },
        400
      )
    }

    // Check if task exists and user has access
    const task = await prisma.task.findUnique({
      where: { id: taskId },
      include: {
        epic: {
          select: { teamId: true },
        },
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

    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: task.epic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to comment on this task',
          },
        },
        403
      )
    }

    const mentions = extractMentions(content)

    const comment = await prisma.comment.create({
      data: {
        content: content.trim(),
        taskId,
        authorId: auth.user!.userId,
      },
      include: {
        author: {
          select: { id: true, username: true },
        },
      },
    })

    // Log activity
    await prisma.activityLog.create({
      data: {
        action: 'comment.added',
        entityType: 'task',
        entityId: taskId,
        actorId: auth.user!.userId,
        payload: JSON.stringify({
          comment_id: comment.id,
          mentions,
        }),
      },
    })

    // Dispatch webhook for comment creation
    dispatchWebhook('comment.created', {
      comment_id: comment.id,
      task_id: taskId,
      content: comment.content,
      author: comment.author,
      mentions,
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    return c.json(
      {
        data: {
          id: comment.id,
          content: comment.content,
          content_html: renderMarkdown(comment.content),
          mentions,
          created_at: comment.createdAt.toISOString(),
          updated_at: comment.updatedAt.toISOString(),
          author: comment.author,
        },
      },
      201
    )
  } catch (error) {
    console.error('Create comment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create comment',
        },
      },
      500
    )
  }
})

// PUT /api/comments/:id - Update a comment
comments.put('/comments/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const { content } = await c.req.json()
    const auth = c.get('auth')

    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Content is required and must be a non-empty string',
          },
        },
        400
      )
    }

    // Check if comment exists
    const existingComment = await prisma.comment.findUnique({
      where: { id },
    })

    if (!existingComment) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Comment not found',
          },
        },
        404
      )
    }

    // Only author or admin can update
    if (existingComment.authorId !== auth.user!.userId && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to update this comment',
          },
        },
        403
      )
    }

    const mentions = extractMentions(content)

    const comment = await prisma.comment.update({
      where: { id },
      data: {
        content: content.trim(),
      },
      include: {
        author: {
          select: { id: true, username: true },
        },
      },
    })

    // Log activity
    await prisma.activityLog.create({
      data: {
        action: 'comment.updated',
        entityType: 'task',
        entityId: existingComment.taskId,
        actorId: auth.user!.userId,
        payload: JSON.stringify({
          comment_id: id,
          before: existingComment.content,
          after: content,
          mentions,
        }),
      },
    })

    // Dispatch webhook for comment update
    dispatchWebhook('comment.updated', {
      comment_id: comment.id,
      task_id: existingComment.taskId,
      content: comment.content,
      author: comment.author,
      before: { content: existingComment.content },
      after: { content: comment.content },
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    return c.json({
      data: {
        id: comment.id,
        content: comment.content,
        content_html: renderMarkdown(comment.content),
        mentions,
        created_at: comment.createdAt.toISOString(),
        updated_at: comment.updatedAt.toISOString(),
        author: comment.author,
      },
    })
  } catch (error) {
    console.error('Update comment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update comment',
        },
      },
      500
    )
  }
})

// DELETE /api/comments/:id - Delete a comment
comments.delete('/comments/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    // Check if comment exists
    const comment = await prisma.comment.findUnique({
      where: { id },
    })

    if (!comment) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Comment not found',
          },
        },
        404
      )
    }

    // Only author or admin can delete
    if (comment.authorId !== auth.user!.userId && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to delete this comment',
          },
        },
        403
      )
    }

    // Log activity before deletion
    await prisma.activityLog.create({
      data: {
        action: 'comment.deleted',
        entityType: 'task',
        entityId: comment.taskId,
        actorId: auth.user!.userId,
        payload: JSON.stringify({
          comment_id: id,
          content: comment.content,
        }),
      },
    })

    await prisma.comment.delete({
      where: { id },
    })

    // Dispatch webhook for comment deletion
    dispatchWebhook('comment.deleted', {
      comment_id: id,
      task_id: comment.taskId,
      author_id: comment.authorId,
    }).catch((err) => console.error('Failed to dispatch webhook:', err))

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete comment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete comment',
        },
      },
      500
    )
  }
})

export default comments
