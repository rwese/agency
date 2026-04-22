import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

interface Epic {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'review' | 'blocked' | 'done'
  tags: string[]
  team: { id: string; name: string }
  task_count: number
  completed_task_count: number
  created_at: string
  updated_at: string
  created_by: { id: string; username: string }
}

// Mock data for fallback
const mockEpics: Epic[] = [
  { id: '1', title: 'User Authentication', description: 'Complete authentication system with login, register, and session management', status: 'in_progress', tags: ['security', 'auth'], team: { id: '1', name: 'Backend' }, task_count: 8, completed_task_count: 3, created_at: '2026-04-10T10:00:00Z', updated_at: '2026-04-22T14:30:00Z', created_by: { id: '1', username: 'Alice' } },
  { id: '2', title: 'Dashboard Redesign', description: 'Complete overhaul of the main dashboard with new widgets and improved UX', status: 'review', tags: ['ui', 'design'], team: { id: '2', name: 'Frontend' }, task_count: 12, completed_task_count: 10, created_at: '2026-04-01T09:00:00Z', updated_at: '2026-04-20T11:00:00Z', created_by: { id: '2', username: 'Bob' } },
  { id: '3', title: 'API v2 Migration', description: 'Migrate all endpoints to v2 with improved performance and new features', status: 'open', tags: ['backend', 'api'], team: { id: '1', name: 'Backend' }, task_count: 15, completed_task_count: 0, created_at: '2026-04-15T14:00:00Z', updated_at: '2026-04-15T14:00:00Z', created_by: { id: '1', username: 'Alice' } },
  { id: '4', title: 'Mobile App Beta', description: 'Release mobile app beta with core features', status: 'blocked', tags: ['mobile', 'ios', 'android'], team: { id: '3', name: 'Mobile' }, task_count: 20, completed_task_count: 18, created_at: '2026-03-20T10:00:00Z', updated_at: '2026-04-18T16:00:00Z', created_by: { id: '3', username: 'Carol' } },
  { id: '5', title: 'Performance Optimization', description: 'Optimize database queries and reduce page load times', status: 'done', tags: ['performance', 'database'], team: { id: '1', name: 'Backend' }, task_count: 6, completed_task_count: 6, created_at: '2026-03-01T10:00:00Z', updated_at: '2026-04-10T09:00:00Z', created_by: { id: '1', username: 'Alice' } },
]

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'review', label: 'Review' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'done', label: 'Done' },
]

const teamOptions = [
  { value: '', label: 'All Teams' },
  { value: '1', label: 'Backend' },
  { value: '2', label: 'Frontend' },
  { value: '3', label: 'Mobile' },
]

const statusColors: Record<string, string> = {
  done: 'bg-green-100 text-green-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  review: 'bg-purple-100 text-purple-800',
  blocked: 'bg-red-100 text-red-800',
  open: 'bg-gray-100 text-gray-800',
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

export function EpicsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [teamFilter, setTeamFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch epics
  const { data: epicsData, isLoading } = useQuery({
    queryKey: ['epics', statusFilter, teamFilter, searchQuery],
    queryFn: async () => {
      let endpoint = '/epics?'
      if (statusFilter) endpoint += `status=${statusFilter}&`
      if (teamFilter) endpoint += `team=${teamFilter}&`
      if (searchQuery) endpoint += `search=${encodeURIComponent(searchQuery)}&`
      
      const response = await api.get<{ epics: Epic[] }>(endpoint)
      if (response.error || !response.data) {
        return null
      }
      return response.data.epics
    },
  })

  const epics = epicsData || mockEpics

  const filteredEpics = epics.filter((epic) => {
    if (searchQuery && !epic.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const getProgressPercent = (epic: Epic) => {
    if (epic.task_count === 0) return 0
    return Math.round((epic.completed_task_count / epic.task_count) * 100)
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search epics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <select
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {teamOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
            + New Epic
          </button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Epics Grid */}
      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEpics.map((epic) => (
            <Link
              key={epic.id}
              to={`/epics/${epic.id}`}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-5 block"
            >
              <div className="flex items-start justify-between mb-3">
                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${statusColors[epic.status] || statusColors.open}`}>
                  {epic.status.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-500">{epic.team.name}</span>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1">{epic.title}</h3>
              <p className="text-sm text-gray-600 line-clamp-2 mb-4">{epic.description}</p>
              
              {/* Tags */}
              <div className="flex flex-wrap gap-1 mb-4">
                {epic.tags.slice(0, 3).map(tag => (
                  <span key={tag} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded">
                    {tag}
                  </span>
                ))}
                {epic.tags.length > 3 && (
                  <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                    +{epic.tags.length - 3}
                  </span>
                )}
              </div>
              
              {/* Progress */}
              <div className="mb-2">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progress</span>
                  <span>{epic.completed_task_count}/{epic.task_count} tasks</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${getProgressPercent(epic)}%` }}
                  />
                </div>
              </div>
              
              <div className="flex justify-between text-xs text-gray-500 mt-4 pt-3 border-t border-gray-100">
                <span>by {epic.created_by.username}</span>
                <span>{formatDate(epic.updated_at)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!isLoading && filteredEpics.length === 0 && (
        <div className="text-center py-12 text-gray-500 bg-white rounded-lg shadow">
          No epics found matching your filters.
        </div>
      )}
    </div>
  )
}
