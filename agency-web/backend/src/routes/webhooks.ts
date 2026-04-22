import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, requireAdmin, type Variables } from '../middleware/auth'
import { WEBHOOK_EVENTS, generateWebhookSignature, type WebhookEvent } from '../lib/webhook'

const webhooks = new Hono<{ Variables: Variables }>()

// GET /webhooks - List webhooks (Admin only)
webhooks.get('/', requireAdmin(), async (c) => {
  try {
    const webhookList = await prisma.webhook.findMany({
      orderBy: { createdAt: 'desc' },
      include: {
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    return c.json({
      data: webhookList.map((webhook) => ({
        id: webhook.id,
        name: webhook.name,
        url: webhook.url,
        events: JSON.parse(webhook.events),
        active: webhook.active,
        created_at: webhook.createdAt.toISOString(),
        created_by: webhook.createdBy,
      })),
    })
  } catch (error) {
    console.error('List webhooks error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to list webhooks',
        },
      },
      500
    )
  }
})

// POST /webhooks - Create webhook
webhooks.post('/', requireAuth(), async (c) => {
  try {
    const auth = c.get('auth')
    const { name, url, events, secret } = await c.req.json()

    if (!name) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Name is required',
          },
        },
        400
      )
    }

    if (!url) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'URL is required',
          },
        },
        400
      )
    }

    // Validate URL format
    try {
      new URL(url)
    } catch {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid URL format',
          },
        },
        400
      )
    }

    if (!events || !Array.isArray(events) || events.length === 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Events array is required and must not be empty',
          },
        },
        400
      )
    }

    // Validate event types
    const invalidEvents = events.filter((e: string) => !WEBHOOK_EVENTS.includes(e as WebhookEvent))
    if (invalidEvents.length > 0) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: `Invalid event types: ${invalidEvents.join(', ')}. Valid types: ${WEBHOOK_EVENTS.join(', ')}`,
          },
        },
        400
      )
    }

    if (!secret) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Secret is required for signature verification',
          },
        },
        400
      )
    }

    const webhook = await prisma.webhook.create({
      data: {
        name,
        url,
        events: JSON.stringify(events),
        secret,
        createdById: auth.user!.userId,
      },
      include: {
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    return c.json(
      {
        data: {
          id: webhook.id,
          name: webhook.name,
          url: webhook.url,
          events: JSON.parse(webhook.events),
          active: webhook.active,
          created_at: webhook.createdAt.toISOString(),
          created_by: webhook.createdBy,
        },
      },
      201
    )
  } catch (error) {
    console.error('Create webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to create webhook',
        },
      },
      500
    )
  }
})

// GET /webhooks/:id - Get webhook details
webhooks.get('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    const webhook = await prisma.webhook.findUnique({
      where: { id },
      include: {
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    if (!webhook) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Webhook not found',
          },
        },
        404
      )
    }

    return c.json({
      data: {
        id: webhook.id,
        name: webhook.name,
        url: webhook.url,
        events: JSON.parse(webhook.events),
        active: webhook.active,
        created_at: webhook.createdAt.toISOString(),
        updated_at: webhook.updatedAt.toISOString(),
        created_by: webhook.createdBy,
      },
    })
  } catch (error) {
    console.error('Get webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to get webhook',
        },
      },
      500
    )
  }
})

// PUT /webhooks/:id - Update webhook
webhooks.put('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()
    const { name, url, events, active, secret } = await c.req.json()

    const existing = await prisma.webhook.findUnique({
      where: { id },
    })

    if (!existing) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Webhook not found',
          },
        },
        404
      )
    }

    const updateData: Record<string, any> = {}

    if (name !== undefined) updateData.name = name
    if (url !== undefined) {
      try {
        new URL(url)
        updateData.url = url
      } catch {
        return c.json(
          {
            data: null,
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Invalid URL format',
            },
          },
          400
        )
      }
    }
    if (events !== undefined) {
      if (!Array.isArray(events)) {
        return c.json(
          {
            data: null,
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Events must be an array',
            },
          },
          400
        )
      }
      const invalidEvents = events.filter((e: string) => !WEBHOOK_EVENTS.includes(e as WebhookEvent))
      if (invalidEvents.length > 0) {
        return c.json(
          {
            data: null,
            error: {
              code: 'VALIDATION_ERROR',
              message: `Invalid event types: ${invalidEvents.join(', ')}`,
            },
          },
          400
        )
      }
      updateData.events = JSON.stringify(events)
    }
    if (active !== undefined) updateData.active = active
    if (secret !== undefined) updateData.secret = secret

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

    const webhook = await prisma.webhook.update({
      where: { id },
      data: updateData,
      include: {
        createdBy: {
          select: { id: true, username: true },
        },
      },
    })

    return c.json({
      data: {
        id: webhook.id,
        name: webhook.name,
        url: webhook.url,
        events: JSON.parse(webhook.events),
        active: webhook.active,
        created_at: webhook.createdAt.toISOString(),
        updated_at: webhook.updatedAt.toISOString(),
        created_by: webhook.createdBy,
      },
    })
  } catch (error) {
    console.error('Update webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to update webhook',
        },
      },
      500
    )
  }
})

// DELETE /webhooks/:id - Delete webhook
webhooks.delete('/:id', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    const webhook = await prisma.webhook.findUnique({
      where: { id },
    })

    if (!webhook) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Webhook not found',
          },
        },
        404
      )
    }

    await prisma.webhook.delete({
      where: { id },
    })

    return c.body(null, 204)
  } catch (error) {
    console.error('Delete webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to delete webhook',
        },
      },
      500
    )
  }
})

// POST /webhooks/:id/test - Send test event
webhooks.post('/:id/test', requireAdmin(), async (c) => {
  try {
    const { id } = c.req.param()

    const webhook = await prisma.webhook.findUnique({
      where: { id },
    })

    if (!webhook) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'Webhook not found',
          },
        },
        404
      )
    }

    const testPayload = JSON.stringify({
      event: 'test',
      timestamp: new Date().toISOString(),
      data: {
        message: 'This is a test webhook delivery',
        webhook_id: webhook.id,
      },
    })

    const signature = generateWebhookSignature(testPayload, webhook.secret)
    const startTime = Date.now()

    try {
      const response = await fetch(webhook.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': signature,
          'X-Webhook-Event': 'test',
        },
        body: testPayload,
      })

      const responseTime = Date.now() - startTime

      return c.json({
        data: {
          success: response.ok,
          status_code: response.status,
          response_time_ms: responseTime,
        },
      })
    } catch (error) {
      return c.json({
        data: {
          success: false,
          status_code: 0,
          response_time_ms: Date.now() - startTime,
          error: 'Failed to connect to webhook URL',
        },
      })
    }
  } catch (error) {
    console.error('Test webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to test webhook',
        },
      },
      500
    )
  }
})

export default webhooks
