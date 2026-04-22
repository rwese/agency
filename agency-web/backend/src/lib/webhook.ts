import { prisma } from './prisma'
import crypto from 'crypto'

// Webhook event types
export const WEBHOOK_EVENTS = [
  'epic.created',
  'epic.updated',
  'epic.deleted',
  'epic.status_changed',
  'task.created',
  'task.updated',
  'task.deleted',
  'task.status_changed',
  'task.assigned',
  'task.priority_changed',
  'comment.created',
  'comment.updated',
  'comment.deleted',
] as const

export type WebhookEvent = typeof WEBHOOK_EVENTS[number]

// Helper to generate webhook signature
export function generateWebhookSignature(payload: string, secret: string): string {
  const hmac = crypto.createHmac('sha256', secret)
  hmac.update(payload)
  return `sha256=${hmac.digest('hex')}`
}

// Send webhook payload to registered URLs
export async function dispatchWebhook(
  event: WebhookEvent,
  data: Record<string, any>
): Promise<void> {
  try {
    // Get all active webhooks subscribed to this event
    const webhooks = await prisma.webhook.findMany({
      where: {
        active: true,
      },
    })

    const payload = JSON.stringify({
      event,
      timestamp: new Date().toISOString(),
      data,
    })

    // Dispatch to all subscribed webhooks in parallel
    await Promise.all(
      webhooks.map(async (webhook) => {
        try {
          const events = JSON.parse(webhook.events) as string[]
          if (!events.includes(event)) {
            return
          }

          const signature = generateWebhookSignature(payload, webhook.secret)

          const response = await fetch(webhook.url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Webhook-Signature': signature,
              'X-Webhook-Event': event,
            },
            body: payload,
          })

          if (!response.ok) {
            console.error(`Webhook ${webhook.id} delivery failed: ${response.status}`)
          }
        } catch (error) {
          console.error(`Webhook ${webhook.id} delivery error:`, error)
        }
      })
    )
  } catch (error) {
    console.error('Webhook dispatch error:', error)
  }
}
