import { Hono } from 'hono'
import { prisma } from '../lib/prisma'
import { requireAuth, type Variables } from '../middleware/auth'
import crypto from 'crypto'

const github = new Hono<{ Variables: Variables }>()

// Parse GitHub webhook event
interface GitHubIssueEvent {
  action: string
  issue: {
    number: number
    title: string
    body: string | null
    state: string
    html_url: string
    labels?: Array<{ name: string }>
  }
  repository: {
    full_name: string
  }
  sender?: {
    login: string
  }
}

interface GitHubPREvent {
  action: string
  pull_request: {
    number: number
    title: string
    body: string | null
    state: string
    html_url: string
    merged: boolean
  }
  repository: {
    full_name: string
  }
  sender?: {
    login: string
  }
}

// Find task by GitHub reference
async function findTaskByGitHubRef(
  repoFullName: string,
  issueNumber: number,
  refType: 'issue' | 'pull_request'
): Promise<{ taskId: string; externalId: string } | null> {
  const externalId = `github:${repoFullName}#${issueNumber}`

  const task = await prisma.task.findFirst({
    where: {
      externalId: externalId,
    },
    select: { id: true, externalId: true },
  })

  if (task) {
    return { taskId: task.id, externalId: task.externalId! }
  }

  // Also try to find by partial match for merged PRs
  if (refType === 'pull_request') {
    const partialMatch = await prisma.task.findFirst({
      where: {
        externalId: {
          contains: `github:${repoFullName}`,
        },
      },
      select: { id: true, externalId: true },
    })

    if (partialMatch) {
      return { taskId: partialMatch.id, externalId: partialMatch.externalId! }
    }
  }

  return null
}

// Create a new task from GitHub issue
async function createTaskFromGitHubIssue(
  event: GitHubIssueEvent,
  actorId: string
): Promise<string> {
  const repoFullName = event.repository.full_name
  const issue = event.issue
  const externalId = `github:${repoFullName}#${issue.number}`

  // Find a default team or create a placeholder
  // In a real implementation, you'd have a team mapping for GitHub repos
  const team = await prisma.team.findFirst({
    orderBy: { createdAt: 'asc' },
    take: 1,
  })

  if (!team) {
    throw new Error('No team found to assign GitHub issue')
  }

  // Check if there's a default epic for GitHub issues
  let epic = await prisma.epic.findFirst({
    where: {
      teamId: team.id,
      title: {
        contains: 'GitHub',
      },
    },
    take: 1,
  })

  // Create a default epic if none exists
  if (!epic) {
    epic = await prisma.epic.create({
      data: {
        title: 'GitHub Issues',
        description: 'Issues synced from GitHub',
        teamId: team.id,
        createdById: actorId,
      },
    })
  }

  // Extract tags from GitHub labels
  const tags = issue.labels?.map((l) => l.name) || []

  const task = await prisma.task.create({
    data: {
      title: issue.title,
      description: issue.body || '',
      status: issue.state === 'open' ? 'open' : 'done',
      tags: tags.length > 0 ? JSON.stringify(tags) : null,
      externalId,
      epicId: epic.id,
      createdById: actorId,
    },
  })

  return task.id
}

// Sync GitHub issue to task
async function syncGitHubIssue(
  event: GitHubIssueEvent,
  refType: 'issue' | 'pull_request'
): Promise<{ task_id: string; synced: boolean; action: string }> {
  const repoFullName = event.repository.full_name
  const issueNumber = event.issue.number
  const action = event.action

  // Find existing task
  const existing = await findTaskByGitHubRef(repoFullName, issueNumber, refType)

  // Handle different GitHub actions
  switch (action) {
    case 'opened':
    case 'created':
      if (existing) {
        // Update existing task
        await prisma.task.update({
          where: { id: existing.taskId },
          data: {
            title: event.issue.title,
            description: event.issue.body || '',
            status: event.issue.state === 'open' ? 'open' : 'done',
          },
        })
        return { task_id: existing.taskId, synced: true, action: 'updated' }
      } else {
        // Get automation user or first admin
        const user = await prisma.user.findFirst({
          where: { role: 'automation' },
        }) || await prisma.user.findFirst({
          where: { role: 'admin' },
        })

        if (!user) {
          throw new Error('No user found to create task')
        }

        const taskId = await createTaskFromGitHubIssue(event, user.id)
        return { task_id: taskId, synced: true, action: 'created' }
      }

    case 'closed':
      if (existing) {
        await prisma.task.update({
          where: { id: existing.taskId },
          data: {
            status: 'done',
          },
        })
        return { task_id: existing.taskId, synced: true, action: 'closed' }
      }
      break

    case 'reopened':
      if (existing) {
        await prisma.task.update({
          where: { id: existing.taskId },
          data: {
            status: 'open',
          },
        })
        return { task_id: existing.taskId, synced: true, action: 'reopened' }
      }
      break

    case 'labeled':
    case 'unlabeled':
      if (existing) {
        const tags = event.issue.labels?.map((l) => l.name) || []
        await prisma.task.update({
          where: { id: existing.taskId },
          data: {
            tags: tags.length > 0 ? JSON.stringify(tags) : undefined,
          },
        })
        return { task_id: existing.taskId, synced: true, action }
      }
      break

    case 'assigned':
    case 'unassigned':
      if (existing && event.sender) {
        // Find user by GitHub username or create mapping
        // For now, we'll skip assignee sync as it requires user mapping
        return { task_id: existing.taskId, synced: true, action }
      }
      break

    case 'synchronize': // PR was updated by a push
      if (existing) {
        return { task_id: existing.taskId, synced: true, action }
      }
      break
  }

  return { task_id: '', synced: false, action }
}

// POST /github/sync-issue - Sync a GitHub issue (webhook receiver from GitHub)
github.post('/sync-issue', requireAuth(), async (c) => {
  try {
    const event: GitHubIssueEvent = await c.req.json()

    // Validate required fields
    if (!event.issue || !event.repository) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Missing required fields: issue and repository',
          },
        },
        400
      )
    }

    const result = await syncGitHubIssue(event, 'issue')

    return c.json({
      data: result,
    })
  } catch (error) {
    console.error('GitHub sync error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to sync GitHub issue',
        },
      },
      500
    )
  }
})

// POST /github/webhook - GitHub webhook receiver (handles multiple event types)
github.post('/webhook', async (c) => {
  try {
    // Get GitHub signature from headers
    const signature = c.req.header('X-Hub-Signature-256')
    const eventType = c.req.header('X-GitHub-Event')

    // For GitHub webhooks, we use the API key for auth
    // The webhook URL would be protected by a secret in production
    // For now, we'll accept requests with a valid API key in the header
    const authHeader = c.req.header('Authorization')
    const apiKey = authHeader?.replace('Bearer ', '')

    // Verify API key if provided
    if (apiKey) {
      const user = await prisma.user.findFirst({
        where: {
          apiKeyHash: apiKey,
        },
      })

      if (!user) {
        return c.json(
          {
            data: null,
            error: {
              code: 'UNAUTHORIZED',
              message: 'Invalid API key',
            },
          },
          401
        )
      }
    }

    const rawBody = await c.req.text()
    let payload: Record<string, any>

    try {
      payload = JSON.parse(rawBody)
    } catch {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid JSON payload',
          },
        },
        400
      )
    }

    // Process based on GitHub event type
    switch (eventType) {
      case 'issues':
        if (payload.issue && payload.repository) {
          const result = await syncGitHubIssue(
            payload as GitHubIssueEvent,
            'issue'
          )
          return c.json({ data: result })
        }
        break

      case 'pull_request':
        if (payload.pull_request && payload.repository) {
          const pr = payload.pull_request as GitHubPREvent['pull_request']
          const repoFullName = payload.repository.full_name
          const prNumber = pr.number

          // Find existing task
          const externalId = `github:${repoFullName}#${prNumber}`
          const existing = await prisma.task.findFirst({
            where: { externalId },
          })

          let partial = null
          if (!existing) {
            // Try partial match
            partial = await prisma.task.findFirst({
              where: {
                externalId: { contains: `github:${repoFullName}` },
              },
            })
            if (partial) {
              // Update external ID with full reference
              await prisma.task.update({
                where: { id: partial.id },
                data: { externalId },
              })

              // Add PR reference
              await prisma.gitHubRef.create({
                data: {
                  refType: 'pull_request',
                  refId: `PR #${prNumber}`,
                  url: pr.html_url,
                  taskId: partial.id,
                },
              })
            }
          }

          // Update task based on PR state
          if (existing || partial) {
            const taskId = existing?.id ?? partial!.id
            await prisma.task.update({
              where: { id: taskId },
              data: {
                status: pr.merged ? 'done' : pr.state === 'closed' ? 'done' : 'in_progress',
              },
            })

            // Create GitHub ref if it doesn't exist
            const existingRef = await prisma.gitHubRef.findFirst({
              where: {
                taskId,
                refType: 'pull_request',
                refId: `PR #${prNumber}`,
              },
            })

            if (!existingRef) {
              await prisma.gitHubRef.create({
                data: {
                  refType: 'pull_request',
                  refId: `PR #${prNumber}`,
                  url: pr.html_url,
                  taskId,
                },
              })
            }
          }

          return c.json({
            data: {
              task_id: existing?.id || partial?.id || null,
              synced: true,
              action: payload.action,
            },
          })
        }
        break

      case 'push':
        if (payload.commits && payload.repository) {
          const repoFullName = payload.repository.full_name
          const commits = payload.commits as Array<{
            id: string
            message: string
            url: string
          }>

          // Find tasks linked to this repo and add commit references
          const tasks = await prisma.task.findMany({
            where: {
              externalId: { contains: `github:${repoFullName}` },
            },
          })

          for (const task of tasks) {
            for (const commit of commits.slice(0, 5)) {
              // Limit to 5 commits per push
              const existingRef = await prisma.gitHubRef.findFirst({
                where: {
                  taskId: task.id,
                  refType: 'commit',
                  refId: commit.id.slice(0, 12),
                },
              })

              if (!existingRef) {
                await prisma.gitHubRef.create({
                  data: {
                    refType: 'commit',
                    refId: commit.id.slice(0, 12),
                    url: commit.url,
                    taskId: task.id,
                  },
                })
              }
            }
          }

          return c.json({
            data: {
              synced: true,
              commits_processed: commits.length,
              tasks_updated: tasks.length,
            },
          })
        }
        break

      default:
        return c.json({
          data: {
            message: `Event ${eventType} received but not processed`,
          },
        })
    }

    return c.json({
      data: {
        message: 'Event processed',
      },
    })
  } catch (error) {
    console.error('GitHub webhook error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to process GitHub webhook',
        },
      },
      500
    )
  }
})

// POST /github/sync-pr - Sync a GitHub pull request
github.post('/sync-pr', requireAuth(), async (c) => {
  try {
    const event: GitHubPREvent = await c.req.json()

    if (!event.pull_request || !event.repository) {
      return c.json(
        {
          data: null,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Missing required fields: pull_request and repository',
          },
        },
        400
      )
    }

    const repoFullName = event.repository.full_name
    const prNumber = event.pull_request.number
    const externalId = `github:${repoFullName}#${prNumber}`

    // Find existing task
    let task = await prisma.task.findFirst({
      where: { externalId },
    })

    if (!task) {
      // Try partial match
      task = await prisma.task.findFirst({
        where: {
          externalId: { contains: `github:${repoFullName}` },
        },
      })

      if (task) {
        // Update to full reference
        await prisma.task.update({
          where: { id: task.id },
          data: { externalId },
        })
      }
    }

    if (!task) {
      return c.json(
        {
          data: null,
          error: {
            code: 'NOT_FOUND',
            message: 'No task found linked to this pull request',
          },
        },
        404
      )
    }

    const pr = event.pull_request

    // Update task status based on PR state
    const status = pr.merged ? 'done' : pr.state === 'closed' ? 'done' : 'in_progress'

    await prisma.task.update({
      where: { id: task.id },
      data: { status },
    })

    // Add PR reference
    await prisma.gitHubRef.upsert({
      where: {
        taskId_refType_refId: {
          taskId: task.id,
          refType: 'pull_request',
          refId: `PR #${prNumber}`,
        },
      },
      create: {
        refType: 'pull_request',
        refId: `PR #${prNumber}`,
        url: pr.html_url,
        taskId: task.id,
      },
      update: {
        url: pr.html_url,
      },
    })

    return c.json({
      data: {
        task_id: task.id,
        synced: true,
        action: event.action,
      },
    })
  } catch (error) {
    console.error('GitHub PR sync error:', error)
    return c.json(
      {
        data: null,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to sync GitHub pull request',
        },
      },
      500
    )
  }
})

export default github
