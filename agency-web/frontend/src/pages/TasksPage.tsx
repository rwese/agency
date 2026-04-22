import { useState } from 'react'
import { Link } from 'react-router-dom'

interface Task {
  id: string
  title: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee?: { id: string; username: string }
  epic?: { id: string; title: string }
  created_at: string
}

// Mock data
const mockTasks: Task[] = [
  { id: '1', title: 'Implement user authentication', status: 'in_progress', priority: 'high', assignee: { id: '1', username: 'John' }, epic: { id: '1', title: 'Auth System' }, created_at: '2024-01-15' },
  { id: '2', title: 'Design dashboard layout', status: 'done', priority: 'medium', assignee: { id: '2', username: 'Jane' }, epic: { id: '2', title: 'UI Redesign' }, created_at: '2024-01-14' },
  { id: '3', title: 'Setup CI/CD pipeline', status: 'todo', priority: 'low', assignee: { id: '3', username: 'Bob' }, created_at: '2024-01-13' },
  { id: '4', title: 'Write unit tests', status: 'review', priority: 'medium', assignee: { id: '1', username: 'John' }, created_at: '2024-01-12' },
  { id: '5', title: 'Fix login bug', status: 'done', priority: 'critical', assignee: { id: '2', username: 'Jane' }, created_at: '2024-01-11' },
]

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'review', label: 'Review' },
  { value: 'done', label: 'Done' },
]

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

export function TasksPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredTasks = mockTasks.filter((task) => {
    if (statusFilter && task.status !== statusFilter) return false
    if (priorityFilter && task.priority !== priorityFilter) return false
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search tasks..."
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
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {priorityOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <Link
            to="/tasks/new"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
          >
            + New Task
          </Link>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assignee</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Epic</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTasks.map((task) => (
              <tr key={task.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <Link to={`/tasks/${task.id}`} className="text-blue-600 hover:text-blue-800 font-medium">
                    {task.title}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full
                    ${task.status === 'done' ? 'bg-green-100 text-green-800' : ''}
                    ${task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' : ''}
                    ${task.status === 'review' ? 'bg-purple-100 text-purple-800' : ''}
                    ${task.status === 'todo' ? 'bg-gray-100 text-gray-800' : ''}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full
                    ${task.priority === 'critical' ? 'bg-red-100 text-red-800' : ''}
                    ${task.priority === 'high' ? 'bg-orange-100 text-orange-800' : ''}
                    ${task.priority === 'medium' ? 'bg-blue-100 text-blue-800' : ''}
                    ${task.priority === 'low' ? 'bg-gray-100 text-gray-800' : ''}`}>
                    {task.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {task.assignee?.username || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {task.epic ? (
                    <Link to={`/epics/${task.epic.id}`} className="text-blue-600 hover:text-blue-800">
                      {task.epic.title}
                    </Link>
                  ) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredTasks.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No tasks found matching your filters.
          </div>
        )}
      </div>
    </div>
  )
}
