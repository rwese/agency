import { PrismaClient, UserRole, EntityStatus, TaskPriority, GitHubRefType } from '@prisma/client'
import * as bcrypt from 'bcrypt'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting database seed...')

  // Create admin user
  const adminPassword = await bcrypt.hash('admin123', 10)
  const admin = await prisma.user.upsert({
    where: { email: 'admin@agency.local' },
    update: {},
    create: {
      username: 'admin',
      email: 'admin@agency.local',
      passwordHash: adminPassword,
      role: UserRole.admin,
    },
  })
  console.log(`✅ Created admin user: ${admin.email}`)

  // Create demo member
  const memberPassword = await bcrypt.hash('member123', 10)
  const member = await prisma.user.upsert({
    where: { email: 'dev@agency.local' },
    update: {},
    create: {
      username: 'developer',
      email: 'dev@agency.local',
      passwordHash: memberPassword,
      role: UserRole.member,
    },
  })
  console.log(`✅ Created member user: ${member.email}`)

  // Create automation user (API-only)
  const automation = await prisma.user.upsert({
    where: { email: 'ci-bot@agency.local' },
    update: {},
    create: {
      username: 'ci-bot',
      email: 'ci-bot@agency.local',
      role: UserRole.automation,
      apiKeyHash: await bcrypt.hash('sk-automation-api-key-demo', 10),
    },
  })
  console.log(`✅ Created automation user: ${automation.email}`)

  // Create a team
  const team = await prisma.team.upsert({
    where: { name: 'Platform Team' },
    update: {},
    create: {
      name: 'Platform Team',
      description: 'Core platform development team',
    },
  })
  console.log(`✅ Created team: ${team.name}`)

  // Add members to team
  await prisma.userTeam.upsert({
    where: {
      userId_teamId: {
        userId: admin.id,
        teamId: team.id,
      },
    },
    update: {},
    create: {
      userId: admin.id,
      teamId: team.id,
      role: 'admin',
    },
  })

  await prisma.userTeam.upsert({
    where: {
      userId_teamId: {
        userId: member.id,
        teamId: team.id,
      },
    },
    update: {},
    create: {
      userId: member.id,
      teamId: team.id,
      role: 'member',
    },
  })
  console.log(`✅ Added members to team: ${team.name}`)

  // Create epics
  const epic1 = await prisma.epic.upsert({
    where: { id: 'epic-auth-system' },
    update: {},
    create: {
      id: 'epic-auth-system',
      title: 'Authentication System',
      description: 'Implement complete authentication system with JWT and API keys',
      status: EntityStatus.in_progress,
      tags: JSON.stringify(['security', 'auth', 'jwt']),
      teamId: team.id,
      createdById: admin.id,
    },
  })

  const epic2 = await prisma.epic.upsert({
    where: { id: 'epic-api-v1' },
    update: {},
    create: {
      id: 'epic-api-v1',
      title: 'API v1 Endpoints',
      description: 'All REST API endpoints for the application',
      status: EntityStatus.open,
      tags: JSON.stringify(['api', 'rest', 'backend']),
      teamId: team.id,
      createdById: admin.id,
    },
  })
  console.log(`✅ Created epics`)

  // Create tasks
  const task1 = await prisma.task.upsert({
    where: { id: 'task-login' },
    update: {},
    create: {
      id: 'task-login',
      title: 'Implement login endpoint',
      description: 'Create POST /api/auth/login with JWT token generation',
      status: EntityStatus.done,
      priority: TaskPriority.high,
      tags: JSON.stringify(['auth', 'jwt']),
      epicId: epic1.id,
      assigneeId: admin.id,
      createdById: admin.id,
    },
  })

  const task2 = await prisma.task.upsert({
    where: { id: 'task-logout' },
    update: {},
    create: {
      id: 'task-logout',
      title: 'Implement logout endpoint',
      description: 'Create POST /api/auth/logout to invalidate tokens',
      status: EntityStatus.in_progress,
      priority: TaskPriority.medium,
      tags: JSON.stringify(['auth', 'jwt']),
      epicId: epic1.id,
      assigneeId: member.id,
      createdById: admin.id,
    },
  })

  const task3 = await prisma.task.upsert({
    where: { id: 'task-users-crud' },
    update: {},
    create: {
      id: 'task-users-crud',
      title: 'User CRUD endpoints',
      description: 'Implement all user management endpoints',
      status: EntityStatus.open,
      priority: TaskPriority.high,
      tags: JSON.stringify(['api', 'users']),
      epicId: epic2.id,
      createdById: admin.id,
    },
  })
  console.log(`✅ Created tasks`)

  // Create comments
  await prisma.comment.upsert({
    where: { id: 'comment-task1-1' },
    update: {},
    create: {
      id: 'comment-task1-1',
      content: 'Login endpoint is complete. Using bcrypt for password hashing.',
      taskId: task1.id,
      authorId: admin.id,
    },
  })

  await prisma.comment.upsert({
    where: { id: 'comment-task2-1' },
    update: {},
    create: {
      id: 'comment-task2-1',
      content: 'Working on token invalidation. Should we use a blacklist or short expiry?',
      taskId: task2.id,
      authorId: member.id,
    },
  })
  console.log(`✅ Created comments`)

  // Create GitHub refs
  await prisma.gitHubRef.upsert({
    where: {
      taskId_refType_refId: {
        taskId: task1.id,
        refType: GitHubRefType.commit,
        refId: 'abc123def456',
      },
    },
    update: {},
    create: {
      refType: GitHubRefType.commit,
      refId: 'abc123def456',
      url: 'https://github.com/agency/web/commit/abc123def456',
      taskId: task1.id,
    },
  })

  await prisma.gitHubRef.upsert({
    where: {
      taskId_refType_refId: {
        taskId: task1.id,
        refType: GitHubRefType.pull_request,
        refId: '42',
      },
    },
    update: {},
    create: {
      refType: GitHubRefType.pull_request,
      refId: '42',
      url: 'https://github.com/agency/web/pull/42',
      taskId: task1.id,
    },
  })
  console.log(`✅ Created GitHub refs`)

  // Create webhook
  await prisma.webhook.upsert({
    where: { id: 'webhook-github' },
    update: {},
    create: {
      id: 'webhook-github',
      name: 'GitHub Webhook',
      url: 'https://agency.local/api/webhooks/github',
      events: JSON.stringify(['push', 'pull_request', 'issues']),
      secret: 'github-webhook-secret-demo',
      active: true,
      createdById: admin.id,
    },
  })
  console.log(`✅ Created webhook`)

  // Create activity logs
  await prisma.activityLog.createMany({
    data: [
      {
        action: 'user.created',
        entityType: 'user',
        entityId: admin.id,
        actorId: admin.id,
        payload: JSON.stringify({ username: 'admin', role: 'admin' }),
      },
      {
        action: 'team.created',
        entityType: 'team',
        entityId: team.id,
        actorId: admin.id,
        payload: JSON.stringify({ name: 'Platform Team' }),
      },
      {
        action: 'epic.created',
        entityType: 'epic',
        entityId: epic1.id,
        actorId: admin.id,
        payload: JSON.stringify({ title: 'Authentication System' }),
      },
      {
        action: 'task.created',
        entityType: 'task',
        entityId: task1.id,
        actorId: admin.id,
        payload: JSON.stringify({ title: 'Implement login endpoint' }),
      },
      {
        action: 'task.status_changed',
        entityType: 'task',
        entityId: task1.id,
        actorId: admin.id,
        payload: JSON.stringify({ from: 'open', to: 'done' }),
      },
    ],
    skipDuplicates: true,
  })
  console.log(`✅ Created activity logs`)

  console.log('\n🎉 Database seed completed successfully!')
  console.log('\n📋 Demo credentials:')
  console.log('   Admin: admin@agency.local / admin123')
  console.log('   Member: dev@agency.local / member123')
  console.log('   Automation: ci-bot@agency.local (API key auth only)')
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
