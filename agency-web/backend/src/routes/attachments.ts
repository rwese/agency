import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, type Variables } from '../middleware/auth'
import { createReadStream, statSync, unlinkSync, existsSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { createHash } from 'crypto'
import { fileURLToPath } from 'url'

const attachments = new Hono<{ Variables: Variables }>()

// Get the directory for storing uploads
function getUploadDir(): string {
  const __dirname = dirname(fileURLToPath(import.meta.url))
  const uploadDir = join(__dirname, '../../uploads')
  if (!existsSync(uploadDir)) {
    mkdirSync(uploadDir, { recursive: true })
  }
  return uploadDir
}

// Generate unique storage path
function generateStoragePath(filename: string): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  const ext = filename.split('.').pop() || ''
  return `${timestamp}-${random}${ext ? '.' + ext : ''}`
}

// Calculate file checksum (MD5)
function calculateChecksum(buffer: Buffer): string {
  return createHash('md5').update(buffer).digest('hex')
}

// POST /api/tasks/:taskId/attachments - Upload attachment
attachments.post('/tasks/:taskId/attachments', requireAuth(), async (c) => {
  try {
    const { taskId } = c.req.param()
    const auth = c.get('auth')

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
            message: 'Not authorized to upload attachments to this task',
          },
        },
        403
      )
    }

    // Parse multipart form data
    const contentType = c.req.header('content-type') || ''
    if (!contentType.includes('multipart/form-data')) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Content-Type must be multipart/form-data',
          },
        },
        400
      )
    }

    // Get form data from request body (Hono's standard parsing)
    const body = await c.req.parseBody()
    const file = body['file']

    if (!file || !(file instanceof File)) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'File is required',
          },
        },
        400
      )
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'File size exceeds maximum limit of 10MB',
          },
        },
        400
      )
    }

    // Read file content
    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)
    const checksum = calculateChecksum(buffer)

    // Generate storage path and save file
    const storagePath = generateStoragePath(file.name)
    const uploadDir = getUploadDir()
    const fullPath = join(uploadDir, storagePath)

    // Write file to disk
    const { writeFileSync } = await import('fs')
    writeFileSync(fullPath, buffer)

    // Create database record
    const attachment = await prisma.attachment.create({
      data: {
        filename: file.name,
        contentType: file.type || 'application/octet-stream',
        sizeBytes: file.size,
        storagePath,
        checksum,
        taskId,
        uploadedById: auth.user!.userId,
      },
      include: {
        uploadedBy: {
          select: { id: true, username: true },
        },
      },
    })

    // Log activity
    await prisma.activityLog.create({
      data: {
        action: 'attachment.uploaded',
        entityType: 'task',
        entityId: taskId,
        actorId: auth.user!.userId,
        payload: JSON.stringify({
          attachment_id: attachment.id,
          filename: file.name,
          size_bytes: file.size,
        }),
      },
    })

    return c.json(
      {
        data: {
          id: attachment.id,
          filename: attachment.filename,
          content_type: attachment.contentType,
          size_bytes: attachment.sizeBytes,
          checksum: attachment.checksum,
          uploaded_at: attachment.uploadedAt.toISOString(),
          uploaded_by: attachment.uploadedBy,
        },
      },
      201
    )
  } catch (error) {
    console.error('Upload attachment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to upload attachment',
        },
      },
      500
    )
  }
})

// GET /api/attachments/:id - Download/get attachment
attachments.get('/attachments/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')
    const download = c.req.query('download') === 'true'

    const attachment = await prisma.attachment.findUnique({
      where: { id },
      include: {
        task: {
          include: {
            epic: {
              select: { teamId: true },
            },
          },
        },
        uploadedBy: {
          select: { id: true, username: true },
        },
      },
    })

    if (!attachment) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Attachment not found',
          },
        },
        404
      )
    }

    // Check access to the task's team
    const userTeam = await prisma.userTeam.findUnique({
      where: {
        userId_teamId: {
          userId: auth.user!.userId,
          teamId: attachment.task.epic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to access this attachment',
          },
        },
        403
      )
    }

    // Check if file exists on disk
    const uploadDir = getUploadDir()
    const fullPath = join(uploadDir, attachment.storagePath)

    if (!existsSync(fullPath)) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'File not found on storage',
          },
        },
        404
      )
    }

    if (download) {
      // Stream the file for download
      const fileStat = statSync(fullPath)
      const stream = createReadStream(fullPath)
      
      return new Response(stream as any, {
        headers: {
          'Content-Type': attachment.contentType,
          'Content-Disposition': `attachment; filename="${attachment.filename}"`,
          'Content-Length': String(fileStat.size),
        },
      })
    }

    // Return metadata only
    return c.json({
      data: {
        id: attachment.id,
        filename: attachment.filename,
        content_type: attachment.contentType,
        size_bytes: attachment.sizeBytes,
        checksum: attachment.checksum,
        uploaded_at: attachment.uploadedAt.toISOString(),
        uploaded_by: attachment.uploadedBy,
        task_id: attachment.taskId,
      },
    })
  } catch (error) {
    console.error('Get attachment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get attachment',
        },
      },
      500
    )
  }
})

// GET /api/attachments/:id/file - Stream file content
attachments.get('/attachments/:id/file', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    const attachment = await prisma.attachment.findUnique({
      where: { id },
      include: {
        task: {
          include: {
            epic: {
              select: { teamId: true },
            },
          },
        },
      },
    })

    if (!attachment) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Attachment not found',
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
          teamId: attachment.task.epic.teamId,
        },
      },
    })

    if (!userTeam && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to access this attachment',
          },
        },
        403
      )
    }

    // Stream the file
    const uploadDir = getUploadDir()
    const fullPath = join(uploadDir, attachment.storagePath)

    if (!existsSync(fullPath)) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'File not found on storage',
          },
        },
        404
      )
    }

    const fileStat = statSync(fullPath)

    const stream = createReadStream(fullPath)

    return new Response(stream as any, {
      headers: {
        'Content-Type': attachment.contentType,
        'Content-Length': String(fileStat.size),
        'Cache-Control': 'public, max-age=31536000',
      },
    })
  } catch (error) {
    console.error('Stream attachment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to stream attachment',
        },
      },
      500
    )
  }
})

// DELETE /api/attachments/:id - Delete attachment
attachments.delete('/attachments/:id', requireAuth(), async (c) => {
  try {
    const { id } = c.req.param()
    const auth = c.get('auth')

    const attachment = await prisma.attachment.findUnique({
      where: { id },
    })

    if (!attachment) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Attachment not found',
          },
        },
        404
      )
    }

    // Only uploader or admin can delete
    if (attachment.uploadedById !== auth.user!.userId && !auth.isAdmin) {
      return c.json(
        {
          data: null,
          error: {
            code: 'FORBIDDEN',
            message: 'Not authorized to delete this attachment',
          },
        },
        403
      )
    }

    // Delete file from disk
    const uploadDir = getUploadDir()
    const fullPath = join(uploadDir, attachment.storagePath)
    if (existsSync(fullPath)) {
      unlinkSync(fullPath)
    }

    // Delete database record
    await prisma.attachment.delete({
      where: { id },
    })

    // Log activity
    await prisma.activityLog.create({
      data: {
        action: 'attachment.deleted',
        entityType: 'task',
        entityId: attachment.taskId,
        actorId: auth.user!.userId,
        payload: JSON.stringify({
          attachment_id: id,
          filename: attachment.filename,
        }),
      },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete attachment error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete attachment',
        },
      },
      500
    )
  }
})

export default attachments
