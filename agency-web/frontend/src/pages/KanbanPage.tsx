import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  DragOverEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { api } from '../services/api'

interface Task {
  id: string
  title: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee?: { id: string; username: string }
  epic?: { id: string; title: string }
  created_at: string
}

interface Column {
  id: string
  title: string
  color: string
  bgColor: string
}

const columns: Column[] = [
  { id: 'todo', title: 'Backlog', color: 'bg-gray-500', bgColor: 'bg-gray-50' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-yellow-500', bgColor: 'bg-yellow-50' },
  { id: 'review', title: 'Review', color: 'bg-purple-500', bgColor: 'bg-purple-50' },
  { id: 'done', title: 'Done', color: 'bg-green-500', bgColor: 'bg-green-50' },
]

const priorityColors: Record<string, string> = {
  critical: 'border-l-red-500 bg-red-50',
  high: 'border-l-orange-500 bg-orange-50',
  medium: 'border-l-blue-500 bg-blue-50',
  low: 'border-l-gray-400 bg-white',
}

// Priority badge styles
const priorityBadgeStyles: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-blue-100 text-blue-700',
  low: 'bg-gray-100 text-gray-700',
}

// Mock data for initial state
const mockTasks: Task[] = [
  { id: '1', title: 'Implement user authentication', status: 'in_progress', priority: 'high', assignee: { id: '1', username: 'John' }, epic: { id: '1', title: 'Auth System' }, created_at: '2024-01-15' },
  { id: '2', title: 'Design dashboard layout', status: 'done', priority: 'medium', assignee: { id: '2', username: 'Jane' }, epic: { id: '2', title: 'UI Redesign' }, created_at: '2024-01-14' },
  { id: '3', title: 'Setup CI/CD pipeline', status: 'todo', priority: 'low', assignee: { id: '3', username: 'Bob' }, created_at: '2024-01-13' },
  { id: '4', title: 'Write unit tests', status: 'review', priority: 'medium', assignee: { id: '1', username: 'John' }, created_at: '2024-01-12' },
  { id: '5', title: 'Fix login bug', status: 'done', priority: 'critical', assignee: { id: '2', username: 'Jane' }, created_at: '2024-01-11' },
  { id: '6', title: 'API documentation', status: 'todo', priority: 'medium', created_at: '2024-01-09' },
  { id: '7', title: 'Database optimization', status: 'in_progress', priority: 'high', assignee: { id: '3', username: 'Bob' }, created_at: '2024-01-10' },
  { id: '8', title: 'Security audit', status: 'todo', priority: 'critical', created_at: '2024-01-08' },
]

// Sortable task card component
function SortableTaskCard({ task }: { task: Task }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`rounded-lg shadow-sm p-3 cursor-grab active:cursor-grabbing hover:shadow-md transition-all border-l-4 ${
        priorityColors[task.priority]
      } ${isDragging ? 'opacity-50 shadow-lg rotate-2' : ''}`}
    >
      <Link to={`/tasks/${task.id}`} className="block" onClick={(e) => e.stopPropagation()}>
        <p className="font-medium text-gray-900 text-sm mb-2 hover:text-blue-600 line-clamp-2">
          {task.title}
        </p>
      </Link>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded ${priorityBadgeStyles[task.priority]}`}>
            {task.priority}
          </span>
        </div>
        {task.assignee && (
          <div
            className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-medium"
            title={task.assignee.username}
          >
            {task.assignee.username.charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      {task.epic && (
        <div className="mt-2">
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            {task.epic.title}
          </span>
        </div>
      )}
    </div>
  )
}

// Task card for drag overlay
function TaskCardOverlay({ task }: { task: Task }) {
  return (
    <div className={`rounded-lg shadow-xl p-3 border-l-4 ${priorityColors[task.priority]} bg-white rotate-3`}>
      <p className="font-medium text-gray-900 text-sm mb-2 line-clamp-2">
        {task.title}
      </p>
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 text-xs rounded ${priorityBadgeStyles[task.priority]}`}>
          {task.priority}
        </span>
        {task.assignee && (
          <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs">
            {task.assignee.username.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </div>
  )
}

// Droppable column component
function DroppableColumn({
  column,
  tasks,
  isOver,
}: {
  column: Column
  tasks: Task[]
  isOver: boolean
}) {
  return (
    <div
      className={`flex flex-col ${column.bgColor} rounded-lg p-3 min-h-[500px] transition-all ${
        isOver ? 'ring-2 ring-blue-400 ring-opacity-50' : ''
      }`}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-3 px-2">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${column.color}`} />
          <h3 className="font-semibold text-gray-700">{column.title}</h3>
        </div>
        <span className="px-2 py-0.5 text-xs bg-white text-gray-600 rounded-full shadow-sm">
          {tasks.length}
        </span>
      </div>

      {/* Tasks */}
      <SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
        <div className="flex-1 space-y-2 overflow-y-auto">
          {tasks.map(task => (
            <SortableTaskCard key={task.id} task={task} />
          ))}

          {tasks.length === 0 && (
            <div className="flex items-center justify-center h-24 border-2 border-dashed border-gray-300 rounded-lg bg-white">
              <p className="text-sm text-gray-400">Drop tasks here</p>
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

export function KanbanPage() {
  const queryClient = useQueryClient()
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [localTasks, setLocalTasks] = useState<Task[]>(mockTasks)

  // Fetch tasks from API
  const { data: fetchedTasks } = useQuery({
    queryKey: ['kanban-tasks'],
    queryFn: async () => {
      const response = await api.get<{ tasks: Task[] }>('/tasks')
      if (response.error || !response.data) {
        return null
      }
      return response.data.tasks
    },
  })

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: string }) => {
      await api.patch(`/tasks/${taskId}`, { status })
    },
    onError: () => {
      // Revert on error
      queryClient.invalidateQueries({ queryKey: ['kanban-tasks'] })
    },
  })

  const tasks = fetchedTasks || localTasks

  // Group tasks by status
  const tasksByColumn = useMemo(() => {
    const grouped: Record<string, Task[]> = {}
    columns.forEach(col => {
      grouped[col.id] = tasks.filter(t => t.status === col.id)
    })
    return grouped
  }, [tasks])

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const task = tasks.find(t => t.id === active.id)
    if (task) {
      setActiveTask(task)
    }
  }

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event
    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    // Find the columns
    const activeTask = tasks.find(t => t.id === activeId)
    if (!activeTask) return

    // Check if we're over a column (by checking if overId matches a column id)
    const overColumn = columns.find(col => col.id === overId)
    if (overColumn) {
      // Moving to a different column
      if (activeTask.status !== overColumn.id) {
        setLocalTasks(prev => prev.map(t =>
          t.id === activeId ? { ...t, status: overColumn.id as Task['status'] } : t
        ))
      }
      return
    }

    // Check if we're over another task
    const overTask = tasks.find(t => t.id === overId)
    if (overTask && activeTask.status !== overTask.status) {
      setLocalTasks(prev => prev.map(t =>
        t.id === activeId ? { ...t, status: overTask.status } : t
      ))
    }
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveTask(null)

    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    const activeTask = tasks.find(t => t.id === activeId)
    if (!activeTask) return

    // Check if we dropped on a column
    const overColumn = columns.find(col => col.id === overId)
    if (overColumn) {
      updateStatusMutation.mutate({ taskId: activeId, status: overColumn.id })
      return
    }

    // Check if we dropped on another task
    const overTask = tasks.find(t => t.id === overId)
    if (overTask && active.id !== over.id) {
      // Reorder within same column
      const columnTasks = tasksByColumn[activeTask.status]
      const oldIndex = columnTasks.findIndex(t => t.id === activeId)
      const newIndex = columnTasks.findIndex(t => t.id === overId)

      if (oldIndex !== -1 && newIndex !== -1 && oldIndex !== newIndex) {
        const reordered = arrayMove(columnTasks, oldIndex, newIndex)
        setLocalTasks(prev => {
          const otherTasks = prev.filter(t => t.status !== activeTask.status)
          return [...otherTasks, ...reordered]
        })
      }

      // Update status if moving to different column
      if (activeTask.status !== overTask.status) {
        updateStatusMutation.mutate({ taskId: activeId, status: overTask.status })
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with action */}
      <div className="flex justify-end">
        <Link
          to="/tasks/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          + New Task
        </Link>
      </div>

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {columns.map(column => (
            <DroppableColumn
              key={column.id}
              column={column}
              tasks={tasksByColumn[column.id] || []}
              isOver={false}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}
