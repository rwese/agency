import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'

interface Task {
  id: string
  title: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  tags: string[]
  assignee?: { id: string; username: string }
  created_at: string
}

interface Comment {
  id: string
  content: string
  created_at: string
  user: { id: string; username: string }
}

interface Activity {
  id: string
  action: string
  item: string
  user: { username: string }
  created_at: string
}

interface Epic {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'review' | 'blocked' | 'done'
  tags: string[]
  team: { id: string; name: string }
  created_at: string
  updated_at: string
  created_by: { id: string; username: string }
  tasks: Task[]
}

// Mock data
const mockEpic: Epic = {
  id: '1',
  title: 'User Authentication',
  description: 'Complete authentication system with login, register, and session management. This epic covers all authentication-related features including password hashing, JWT tokens, session handling, and OAuth integration.',
  status: 'in_progress',
  tags: ['security', 'auth', 'backend'],
  team: { id: '1', name: 'Backend' },
  created_at: '2026-04-10T10:00:00Z',
  updated_at: '2026-04-22T14:30:00Z',
  created_by: { id: '1', username: 'Alice' },
  tasks: [
    { id: '1', title: 'Design login form', status: 'done', priority: 'high', tags: ['ui'], assignee: { id: '2', username: 'Bob' }, created_at: '2026-04-10' },
    { id: '2', title: 'Implement login API', status: 'done', priority: 'high', tags: ['backend'], assignee: { id: '1', username: 'Alice' }, created_at: '2026-04-11' },
    { id: '3', title: 'Create registration page', status: 'done', priority: 'high', tags: ['ui'], assignee: { id: '2', username: 'Bob' }, created_at: '2026-04-12' },
    { id: '4', title: 'Implement registration API', status: 'in_progress', priority: 'high', tags: ['backend'], assignee: { id: '1', username: 'Alice' }, created_at: '2026-04-13' },
    { id: '5', title: 'Add password reset flow', status: 'in_progress', priority: 'medium', tags: ['backend', 'ui'], assignee: { id: '3', username: 'Carol' }, created_at: '2026-04-14' },
    { id: '6', title: 'Implement JWT tokens', status: 'todo', priority: 'high', tags: ['backend'], assignee: { id: '1', username: 'Alice' }, created_at: '2026-04-15' },
    { id: '7', title: 'Add OAuth providers', status: 'todo', priority: 'medium', tags: ['backend'], assignee: { id: '1', username: 'Alice' }, created_at: '2026-04-16' },
    { id: '8', title: 'Write auth tests', status: 'todo', priority: 'low', tags: ['testing'], created_at: '2026-04-17' },
  ],
}

const mockComments: Comment[] = [
  { id: '1', content: 'Started working on the JWT implementation. Should be ready by end of week.', created_at: '2026-04-22T10:00:00Z', user: { id: '1', username: 'Alice' } },
  { id: '2', content: 'The login page mockups look great! Approved for development.', created_at: '2026-04-21T15:30:00Z', user: { id: '2', username: 'Bob' } },
  { id: '3', content: 'Should we consider adding 2FA support as part of this epic?', created_at: '2026-04-20T09:15:00Z', user: { id: '3', username: 'Carol' } },
]

const mockActivity: Activity[] = [
  { id: '1', action: 'updated status', item: 'User Authentication', user: { username: 'Alice' }, created_at: '2026-04-22T14:30:00Z' },
  { id: '2', action: 'completed', item: 'Implement login API', user: { username: 'Alice' }, created_at: '2026-04-21T16:00:00Z' },
  { id: '3', action: 'created', item: 'Password reset flow', user: { username: 'Carol' }, created_at: '2026-04-21T11:00:00Z' },
  { id: '4', action: 'assigned', item: 'Write auth tests', user: { username: 'Bob' }, created_at: '2026-04-20T14:00:00Z' },
]

const statusOptions = [
  { value: 'open', label: 'Open', color: 'bg-gray-100 text-gray-800' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'review', label: 'Review', color: 'bg-purple-100 text-purple-800' },
  { value: 'blocked', label: 'Blocked', color: 'bg-red-100 text-red-800' },
  { value: 'done', label: 'Done', color: 'bg-green-100 text-green-800' },
]

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-blue-100 text-blue-800',
  low: 'bg-gray-100 text-gray-800',
}

const statusBadgeColors: Record<string, string> = {
  done: 'bg-green-100 text-green-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  review: 'bg-purple-100 text-purple-800',
  todo: 'bg-gray-100 text-gray-800',
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(dateStr)
}

export function EpicDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filterStatus, setFilterStatus] = useState('')
  const [activeTab, setActiveTab] = useState<'tasks' | 'comments' | 'activity'>('tasks')
  const [newComment, setNewComment] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Epic>>({})

  // Fetch epic details
  const { data: epicData, isLoading } = useQuery({
    queryKey: ['epic', id],
    queryFn: async () => {
      const response = await api.get<{ epic: Epic }>(`/epics/${id}`)
      if (response.error || !response.data) {
        return null
      }
      return response.data.epic
    },
  })

  // Fetch comments
  const { data: commentsData } = useQuery({
    queryKey: ['epic-comments', id],
    queryFn: async () => {
      const response = await api.get<{ comments: Comment[] }>(`/epics/${id}/comments`)
      if (response.error || !response.data) {
        return null
      }
      return response.data.comments
    },
  })

  // Fetch activity
  const { data: activityData } = useQuery({
    queryKey: ['epic-activity', id],
    queryFn: async () => {
      const response = await api.get<{ activities: Activity[] }>(`/epics/${id}/activity`)
      if (response.error || !response.data) {
        return null
      }
      return response.data.activities
    },
  })

  // Update epic mutation
  const updateEpicMutation = useMutation({
    mutationFn: async (data: Partial<Epic>) => {
      const response = await api.patch(`/epics/${id}`, data)
      if (response.error) throw new Error(response.error.message)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epic', id] })
      setIsEditing(false)
    },
  })

  // Add comment mutation
  const addCommentMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await api.post(`/epics/${id}/comments`, { content })
      if (response.error) throw new Error(response.error.message)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epic-comments', id] })
      setNewComment('')
    },
  })

  const epic = epicData || mockEpic
  const comments = commentsData || mockComments
  const activity = activityData || mockActivity

  const filteredTasks = epic.tasks.filter((task) => {
    if (filterStatus && task.status !== filterStatus) return false
    return true
  })

  const getProgressPercent = () => {
    if (epic.tasks.length === 0) return 0
    const completed = epic.tasks.filter(t => t.status === 'done').length
    return Math.round((completed / epic.tasks.length) * 100)
  }

  const tasksByStatus = {
    todo: filteredTasks.filter(t => t.status === 'todo'),
    in_progress: filteredTasks.filter(t => t.status === 'in_progress'),
    review: filteredTasks.filter(t => t.status === 'review'),
    done: filteredTasks.filter(t => t.status === 'done'),
  }

  const handleSaveEdit = () => {
    updateEpicMutation.mutate(editForm)
  }

  const handleAddComment = () => {
    if (newComment.trim()) {
      addCommentMutation.mutate(newComment.trim())
    }
  }

  return (
    <div className="space-y-6">
      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate('/epics')}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          ← Back
        </button>
        <button
          onClick={() => {
            setEditForm(epic)
            setIsEditing(true)
          }}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Edit Epic
        </button>
        <button className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors">
          Delete
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!isLoading && (
        <>
          {/* Epic Header */}
          <div className="bg-white rounded-lg shadow p-6">
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input
                    type="text"
                    value={editForm.title || ''}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editForm.description || ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={editForm.status || ''}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value as Epic['status'] })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {statusOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveEdit}
                    disabled={updateEpicMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {updateEpicMutation.isPending ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-2xl font-bold text-gray-900">{epic.title}</h1>
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${statusOptions.find(s => s.value === epic.status)?.color}`}>
                        {epic.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">
                      Created by {epic.created_by.username} • {epic.team.name} • Updated {formatDate(epic.updated_at)}
                    </p>
                  </div>
                </div>

                <p className="text-gray-700 mb-4">{epic.description}</p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {epic.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded bg-blue-50 text-blue-700">
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Progress */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-500 mb-1">
                    <span>Overall Progress</span>
                    <span>{epic.tasks.filter(t => t.status === 'done').length}/{epic.tasks.length} tasks completed</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all"
                      style={{ width: `${getProgressPercent()}%` }}
                    />
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{tasksByStatus.todo.length}</p>
                    <p className="text-sm text-gray-500">To Do</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-600">{tasksByStatus.in_progress.length}</p>
                    <p className="text-sm text-gray-500">In Progress</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">{tasksByStatus.review.length}</p>
                    <p className="text-sm text-gray-500">Review</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{tasksByStatus.done.length}</p>
                    <p className="text-sm text-gray-500">Done</p>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('tasks')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 ${
                    activeTab === 'tasks'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Tasks ({epic.tasks.length})
                </button>
                <button
                  onClick={() => setActiveTab('comments')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 ${
                    activeTab === 'comments'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Comments ({comments.length})
                </button>
                <button
                  onClick={() => setActiveTab('activity')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 ${
                    activeTab === 'activity'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Activity ({activity.length})
                </button>
              </nav>
            </div>

            <div className="p-4">
              {/* Tasks Tab */}
              {activeTab === 'tasks' && (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Statuses</option>
                      {statusOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                    <button className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                      + Add Task
                    </button>
                  </div>

                  {/* Tasks Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assignee</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredTasks.map((task) => (
                          <tr key={task.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <Link to={`/tasks/${task.id}`} className="text-blue-600 hover:text-blue-800 font-medium">
                                {task.title}
                              </Link>
                              {task.tags.length > 0 && (
                                <div className="flex gap-1 mt-1">
                                  {task.tags.map(tag => (
                                    <span key={tag} className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${statusBadgeColors[task.status]}`}>
                                {task.status.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${priorityColors[task.priority]}`}>
                                {task.priority}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {task.assignee ? (
                                <div className="flex items-center gap-2">
                                  <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs">
                                    {task.assignee.username.charAt(0).toUpperCase()}
                                  </div>
                                  <span className="text-sm text-gray-700">{task.assignee.username}</span>
                                </div>
                              ) : (
                                <span className="text-sm text-gray-400">Unassigned</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {filteredTasks.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      No tasks found matching your filters.
                    </div>
                  )}
                </>
              )}

              {/* Comments Tab */}
              {activeTab === 'comments' && (
                <div className="space-y-4">
                  {/* Add comment */}
                  <div className="flex gap-2">
                    <textarea
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Add a comment..."
                      rows={2}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleAddComment}
                      disabled={!newComment.trim() || addCommentMutation.isPending}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 self-end"
                    >
                      {addCommentMutation.isPending ? 'Posting...' : 'Post'}
                    </button>
                  </div>

                  {/* Comments list */}
                  <div className="space-y-4">
                    {comments.map((comment) => (
                      <div key={comment.id} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                          {comment.user.username.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-gray-900">{comment.user.username}</span>
                            <span className="text-xs text-gray-500">{formatTimeAgo(comment.created_at)}</span>
                          </div>
                          <p className="text-gray-700 text-sm">{comment.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {comments.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No comments yet. Be the first to add one!
                    </div>
                  )}
                </div>
              )}

              {/* Activity Tab */}
              {activeTab === 'activity' && (
                <div className="space-y-3">
                  {activity.map((item) => (
                    <div key={item.id} className="flex items-start gap-3 py-2">
                      <div className="w-2 h-2 mt-2 rounded-full bg-blue-500" />
                      <div>
                        <p className="text-sm text-gray-900">
                          <span className="font-medium">{item.user.username}</span>
                          {' '}
                          <span className="text-gray-600">{item.action}</span>
                          {' '}
                          <span className="font-medium">{item.item}</span>
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">{formatTimeAgo(item.created_at)}</p>
                      </div>
                    </div>
                  ))}

                  {activity.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No activity recorded yet.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
