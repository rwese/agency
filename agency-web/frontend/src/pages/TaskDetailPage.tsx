import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'

interface Task {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'review' | 'blocked' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  tags: string[]
  external_id?: string
  created_at: string
  updated_at: string
  epic?: { id: string; title: string }
  team?: { id: string; name: string }
  assignee?: { id: string; username: string }
  created_by?: { id: string; username: string }
  attachment_count: number
  comment_count: number
  github_ref_count: number
}

interface Comment {
  id: string
  content: string
  created_at: string
  updated_at: string
  author: { id: string; username: string }
}

interface Attachment {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  uploaded_at: string
  uploaded_by: { id: string; username: string }
}

interface GitHubRef {
  id: string
  ref_type: 'commit' | 'pull_request' | 'issue'
  ref_id: string
  url: string
  created_at: string
}

// Mock data for demo
const mockTask: Task = {
  id: '1',
  title: 'Implement user authentication',
  description: 'Create a complete authentication system with login, register, and session management. Include password hashing, JWT tokens, and secure session handling.',
  status: 'in_progress',
  priority: 'high',
  tags: ['security', 'auth', 'backend'],
  external_id: 'github:owner/repo#123',
  created_at: '2026-04-15T10:30:00Z',
  updated_at: '2026-04-22T14:30:00Z',
  epic: { id: '1', title: 'User Authentication' },
  team: { id: '1', name: 'Backend' },
  assignee: { id: '1', username: 'John' },
  created_by: { id: '2', username: 'Jane' },
  attachment_count: 2,
  comment_count: 5,
  github_ref_count: 1,
}

const mockComments: Comment[] = [
  { id: '1', content: 'Started working on the login form. Should be ready by end of day.', created_at: '2026-04-20T10:00:00Z', updated_at: '2026-04-20T10:00:00Z', author: { id: '1', username: 'John' } },
  { id: '2', content: 'Great progress! Let me know if you need any help with the JWT implementation.', created_at: '2026-04-20T11:30:00Z', updated_at: '2026-04-20T11:30:00Z', author: { id: '2', username: 'Jane' } },
  { id: '3', content: 'Just pushed the first commit to the auth-feature branch.', created_at: '2026-04-21T09:00:00Z', updated_at: '2026-04-21T09:00:00Z', author: { id: '1', username: 'John' } },
]

const mockAttachments: Attachment[] = [
  { id: '1', filename: 'auth-diagram.png', content_type: 'image/png', size_bytes: 45000, uploaded_at: '2026-04-15T10:30:00Z', uploaded_by: { id: '2', username: 'Jane' } },
  { id: '2', filename: 'requirements.pdf', content_type: 'application/pdf', size_bytes: 120000, uploaded_at: '2026-04-15T10:35:00Z', uploaded_by: { id: '1', username: 'John' } },
]

const mockGitHubRefs: GitHubRef[] = [
  { id: '1', ref_type: 'pull_request', ref_id: 'PR #456', url: 'https://github.com/owner/repo/pull/456', created_at: '2026-04-21T09:05:00Z' },
]

const statusOptions = [
  { value: 'open', label: 'Open', color: 'bg-gray-100 text-gray-800' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'review', label: 'Review', color: 'bg-purple-100 text-purple-800' },
  { value: 'blocked', label: 'Blocked', color: 'bg-red-100 text-red-800' },
  { value: 'done', label: 'Done', color: 'bg-green-100 text-green-800' },
]

const priorityOptions = [
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-800' },
  { value: 'high', label: 'High', color: 'bg-orange-100 text-orange-800' },
  { value: 'medium', label: 'Medium', color: 'bg-blue-100 text-blue-800' },
  { value: 'low', label: 'Low', color: 'bg-gray-100 text-gray-800' },
]

type TabType = 'comments' | 'attachments' | 'github' | 'activity'

export function TaskDetailPage() {
  useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('comments')
  const [newComment, setNewComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // In production, this would fetch from the API
  const task = mockTask
  const comments = mockComments
  const attachments = mockAttachments
  const githubRefs = mockGitHubRefs

  const getStatusColor = (status: string) => {
    return statusOptions.find(s => s.value === status)?.color || 'bg-gray-100 text-gray-800'
  }

  const getPriorityColor = (priority: string) => {
    return priorityOptions.find(p => p.value === priority)?.color || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return
    setIsSubmitting(true)
    // In production, this would POST to the API
    // await api.post(`/tasks/${id}/comments`, { content: newComment })
    setNewComment('')
    setIsSubmitting(false)
  }

  const tabs = [
    { id: 'comments' as const, label: 'Comments', count: comments.length },
    { id: 'attachments' as const, label: 'Attachments', count: attachments.length },
    { id: 'github' as const, label: 'GitHub', count: githubRefs.length },
    { id: 'activity' as const, label: 'Activity', count: 0 },
  ]

  const activityLog = [
    { id: '1', action: 'status_changed', actor: 'John', from: 'open', to: 'in_progress', time: '2026-04-20T10:00:00Z' },
    { id: '2', action: 'assigned', actor: 'Jane', to: 'John', time: '2026-04-15T10:30:00Z' },
    { id: '3', action: 'created', actor: 'Jane', time: '2026-04-15T10:30:00Z' },
  ]

  return (
    <div className="space-y-6">
      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate('/tasks')}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          ← Back
        </button>
        <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          Edit Task
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Task Title & Description */}
          <div className="bg-white rounded-lg shadow p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">{task.title}</h1>
            <div className="flex flex-wrap gap-2 mb-4">
              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${getStatusColor(task.status)}`}>
                {task.status.replace('_', ' ')}
              </span>
              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${getPriorityColor(task.priority)}`}>
                {task.priority}
              </span>
              {task.tags.map(tag => (
                <span key={tag} className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded bg-blue-50 text-blue-700">
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-3 text-sm font-medium border-b-2 ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {tab.label}
                    {tab.count > 0 && (
                      <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                        {tab.count}
                      </span>
                    )}
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-4">
              {/* Comments Tab */}
              {activeTab === 'comments' && (
                <div className="space-y-4">
                  {/* Add Comment */}
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Write a comment..."
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <button
                    onClick={handleSubmitComment}
                    disabled={!newComment.trim() || isSubmitting}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isSubmitting ? 'Posting...' : 'Add Comment'}
                  </button>

                  {/* Comments List */}
                  <div className="space-y-4 mt-4">
                    {comments.map(comment => (
                      <div key={comment.id} className="flex gap-3 p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
                          {comment.author.username.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">{comment.author.username}</span>
                            <span className="text-sm text-gray-500">{formatDate(comment.created_at)}</span>
                          </div>
                          <p className="mt-1 text-gray-700">{comment.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Attachments Tab */}
              {activeTab === 'attachments' && (
                <div className="space-y-3">
                  <button className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200">
                    + Upload Attachment
                  </button>
                  {attachments.map(attachment => (
                    <div key={attachment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">📄</span>
                        <div>
                          <p className="font-medium text-gray-900">{attachment.filename}</p>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(attachment.size_bytes)} • Uploaded by {attachment.uploaded_by.username}
                          </p>
                        </div>
                      </div>
                      <button className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800">
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* GitHub Tab */}
              {activeTab === 'github' && (
                <div className="space-y-3">
                  {task.external_id && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">External Reference</p>
                      <p className="font-medium text-gray-900">{task.external_id}</p>
                    </div>
                  )}
                  {githubRefs.map(ref => (
                    <a
                      key={ref.id}
                      href={ref.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                      <span className="text-2xl">🔗</span>
                      <div>
                        <p className="font-medium text-gray-900">{ref.ref_id}</p>
                        <p className="text-sm text-gray-500">{ref.url}</p>
                      </div>
                    </a>
                  ))}
                </div>
              )}

              {/* Activity Tab */}
              {activeTab === 'activity' && (
                <div className="space-y-4">
                  {activityLog.map((activity, index) => (
                    <div key={activity.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                          {activity.actor.charAt(0).toUpperCase()}
                        </div>
                        {index < activityLog.length - 1 && <div className="w-0.5 h-full bg-gray-200 mt-1" />}
                      </div>
                      <div className="flex-1 pb-4">
                        <p className="text-sm text-gray-900">
                          <span className="font-medium">{activity.actor}</span>
                          {' '}
                          {activity.action === 'status_changed' && (
                            <>changed status from <span className="font-medium">{activity.from}</span> to <span className="font-medium">{activity.to}</span></>
                          )}
                          {activity.action === 'assigned' && (
                            <>assigned to <span className="font-medium">{activity.to}</span></>
                          )}
                          {activity.action === 'created' && (
                            <>created this task</>
                          )}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{formatDate(activity.time)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Task Info */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Details</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-xs text-gray-500">Assignee</dt>
                <dd className="text-sm text-gray-900">
                  {task.assignee ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs">
                        {task.assignee.username.charAt(0).toUpperCase()}
                      </div>
                      {task.assignee.username}
                    </div>
                  ) : 'Unassigned'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Epic</dt>
                <dd className="text-sm text-gray-900">
                  {task.epic && (
                    <Link to={`/epics/${task.epic.id}`} className="text-blue-600 hover:text-blue-800">
                      {task.epic.title}
                    </Link>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Team</dt>
                <dd className="text-sm text-gray-900">{task.team?.name}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Created by</dt>
                <dd className="text-sm text-gray-900">{task.created_by?.username}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Created</dt>
                <dd className="text-sm text-gray-900">{formatDate(task.created_at)}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Updated</dt>
                <dd className="text-sm text-gray-900">{formatDate(task.updated_at)}</dd>
              </div>
            </dl>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Actions</h3>
            <div className="space-y-2">
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="">Change Status...</option>
                {statusOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <button className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Assign to...
              </button>
              <button className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Add to Epic...
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
