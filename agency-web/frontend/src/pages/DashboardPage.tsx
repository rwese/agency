import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

// Types
interface Task {
  id: string
  title: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee?: { id: string; username: string }
  epic?: { id: string; title: string }
  created_at: string
}

interface Epic {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'review' | 'blocked' | 'done'
  task_count: number
  completed_task_count: number
  updated_at: string
}

interface Activity {
  id: string
  action: string
  item: string
  user: { username: string }
  created_at: string
}

interface TaskStats {
  total: number
  open: number
  in_progress: number
  done: number
}

// Status badge styles
const statusStyles: Record<string, string> = {
  done: 'bg-green-100 text-green-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  review: 'bg-purple-100 text-purple-800',
  todo: 'bg-gray-100 text-gray-800',
  open: 'bg-gray-100 text-gray-800',
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

// Loading skeleton component
function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
      <div className="h-8 bg-gray-200 rounded w-16"></div>
    </div>
  )
}

function ListItemSkeleton() {
  return (
    <div className="p-4 flex items-center justify-between animate-pulse">
      <div className="flex-1">
        <div className="h-4 bg-gray-200 rounded w-48 mb-1"></div>
        <div className="h-3 bg-gray-200 rounded w-24"></div>
      </div>
      <div className="h-6 bg-gray-200 rounded w-20"></div>
    </div>
  )
}

export function DashboardPage() {
  // Fetch task stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<TaskStats>('/tasks/stats')
      if (response.error || !response.data) {
        return null
      }
      return response.data
    },
  })

  // Fetch recent tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['dashboard-tasks'],
    queryFn: async () => {
      const response = await api.get<{ tasks: Task[] }>('/tasks?limit=5&sort=created_at:desc')
      if (response.error || !response.data) {
        return null
      }
      return response.data.tasks
    },
  })

  // Fetch recent epics
  const { data: epicsData, isLoading: epicsLoading } = useQuery({
    queryKey: ['dashboard-epics'],
    queryFn: async () => {
      const response = await api.get<{ epics: Epic[] }>('/epics?limit=5&sort=updated_at:desc')
      if (response.error || !response.data) {
        return null
      }
      return response.data.epics
    },
  })

  // Fetch activity feed
  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ['dashboard-activity'],
    queryFn: async () => {
      const response = await api.get<{ activities: Activity[] }>('/activity?limit=10')
      if (response.error || !response.data) {
        return null
      }
      return response.data.activities
    },
  })

  // Fallback mock data for when API is not available
  const mockStats = {
    total: tasksData?.length || 24,
    open: tasksData?.filter(t => t.status === 'todo').length || 8,
    in_progress: tasksData?.filter(t => t.status === 'in_progress').length || 10,
    done: tasksData?.filter(t => t.status === 'done').length || 6,
  }

  const mockTasks: Task[] = [
    { id: '1', title: 'Implement user authentication', status: 'in_progress', priority: 'high', assignee: { id: '1', username: 'John' }, created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
    { id: '2', title: 'Design dashboard layout', status: 'done', priority: 'medium', assignee: { id: '2', username: 'Jane' }, created_at: new Date(Date.now() - 3 * 3600000).toISOString() },
    { id: '3', title: 'Setup CI/CD pipeline', status: 'todo', priority: 'low', assignee: { id: '3', username: 'Bob' }, created_at: new Date(Date.now() - 5 * 3600000).toISOString() },
    { id: '4', title: 'Write unit tests', status: 'review', priority: 'medium', assignee: { id: '1', username: 'John' }, created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
  ]

  const mockEpics: Epic[] = [
    { id: '1', title: 'User Authentication', description: 'Complete authentication system', status: 'in_progress', task_count: 8, completed_task_count: 3, updated_at: new Date(Date.now() - 1 * 3600000).toISOString() },
    { id: '2', title: 'Dashboard Redesign', description: 'Complete overhaul of the main dashboard', status: 'review', task_count: 12, completed_task_count: 10, updated_at: new Date(Date.now() - 4 * 3600000).toISOString() },
  ]

  const mockActivity: Activity[] = [
    { id: '1', action: 'completed', item: 'Setup database schema', user: { username: 'John' }, created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
    { id: '2', action: 'created', item: 'Implement API endpoints', user: { username: 'Jane' }, created_at: new Date(Date.now() - 3 * 3600000).toISOString() },
    { id: '3', action: 'commented on', item: 'Dashboard redesign', user: { username: 'Bob' }, created_at: new Date(Date.now() - 5 * 3600000).toISOString() },
    { id: '4', action: 'assigned', item: 'Testing new features', user: { username: 'Alice' }, created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
  ]

  const tasks = tasksData || mockTasks
  const epics = epicsData || mockEpics
  const activities = activityData || mockActivity
  const stats = statsData || mockStats

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-500">Total Tasks</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-gray-900">{stats.total}</span>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-500">Open</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-blue-600">{stats.open}</span>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-500">In Progress</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-yellow-600">{stats.in_progress}</span>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-500">Completed</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-green-600">{stats.done}</span>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
            <Link to="/tasks" className="text-sm text-blue-600 hover:text-blue-800">
              View all
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {tasksLoading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : tasks.length > 0 ? (
              tasks.slice(0, 5).map((task) => (
                <Link
                  key={task.id}
                  to={`/tasks/${task.id}`}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{task.title}</p>
                    <p className="text-xs text-gray-500">
                      {task.assignee?.username || 'Unassigned'}
                    </p>
                  </div>
                  <span
                    className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusStyles[task.status] || statusStyles.todo}`}
                  >
                    {task.status.replace('_', ' ')}
                  </span>
                </Link>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500">
                No tasks found
              </div>
            )}
          </div>
        </div>

        {/* Recent Epics */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Recent Epics</h2>
            <Link to="/epics" className="text-sm text-blue-600 hover:text-blue-800">
              View all
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {epicsLoading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : epics.length > 0 ? (
              epics.slice(0, 5).map((epic) => (
                <Link
                  key={epic.id}
                  to={`/epics/${epic.id}`}
                  className="block p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{epic.title}</p>
                    <span
                      className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusStyles[epic.status] || statusStyles.open}`}
                    >
                      {epic.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full"
                      style={{ width: `${epic.task_count > 0 ? Math.round((epic.completed_task_count / epic.task_count) * 100) : 0}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {epic.completed_task_count}/{epic.task_count} tasks
                  </p>
                </Link>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500">
                No epics found
              </div>
            )}
          </div>
        </div>

        {/* Activity Feed - Full Width on large screens */}
        <div className="bg-white rounded-lg shadow lg:col-span-2">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Activity Feed</h2>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {activityLoading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : activities.length > 0 ? (
              activities.map((activity) => (
                <div key={activity.id} className="p-4">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{activity.user.username}</span>
                    {' '}
                    <span className="text-gray-600">{activity.action}</span>
                    {' '}
                    <span className="font-medium">{activity.item}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatTimeAgo(activity.created_at)}
                  </p>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500">
                No recent activity
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
