# agency-web UI Wireframes

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Draft  

---

## Page Overview

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Authentication |
| Dashboard | `/` | Overview with assigned tasks |
| Epics List | `/epics` | All epics with status |
| Epic Detail | `/epics/{id}` | Epic with its tasks |
| Tasks List | `/tasks` | All tasks with filters |
| Task Detail | `/tasks/{id}` | Task with comments/attachments |
| Admin Users | `/admin/users` | User management |
| Profile | `/profile` | Current user settings |

---

## Page Layouts

### Layout Shell (All Pages)

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  agency-web              [User ▼]  [Logout]        │  ← Header (64px)
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────────────────────────────────────────┐ │
│ │ Nav     │ │                                             │ │
│ │         │ │                                             │ │
│ │ • Dash  │ │              Main Content                   │ │
│ │ • Epics │ │                                             │ │
│ │ • Tasks │ │                                             │ │
│ │         │ │                                             │ │
│ │ ─────── │ │                                             │ │
│ │ Admin   │ │                                             │ │
│ │ • Users │ │                                             │ │
│ └─────────┘ └─────────────────────────────────────────────┘ │  ← Sidebar (240px) + Content
└─────────────────────────────────────────────────────────────┘
```

**Navigation:**
- Dashboard (home icon)
- Epics (folder icon)
- Tasks (checkbox icon)
- **Admin section** (only for admin role)
  - Users (people icon)

**User dropdown:**
- Profile
- Logout

---

## Page: Login

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│                      [Logo]                                 │
│                    agency-web                               │
│                                                             │
│              ┌────────────────────────────┐                 │
│              │  Username                  │                 │
│              └────────────────────────────┘                 │
│              ┌────────────────────────────┐                 │
│              │  Password                  │                 │
│              └────────────────────────────┘                 │
│                                                             │
│              ┌────────────────────────────┐                 │
│              │         Log In             │                 │
│              └────────────────────────────┘                 │
│                                                             │
│              Forgot password? | API Access                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**States:**
- Default: Empty form
- Loading: Button shows spinner, inputs disabled
- Error: Red border on invalid field, error message below

---

## Page: Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                              [+ New Epic] [+ New Task] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ My Tasks            │  │ My Epics            │           │
│  │ ████████░░ 8/10     │  │ ████░░░░░ 2/5       │           │
│  │ open: 3 | review: 2 │  │ in_progress: 2      │           │
│  └─────────────────────┘  └─────────────────────┘           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ My Assigned Tasks                                    │   │
│  ├──────┬────────────────────────┬──────────┬──────────┤   │
│  │ ID   │ Title                  │ Epic     │ Status   │   │
│  ├──────┼────────────────────────┼──────────┼──────────┤   │
│  │ T-42 │ Implement login form   │ Auth     │ ● Open   │   │
│  │ T-44 │ Add unit tests         │ Auth     │ ● Review │   │
│  │ T-51 │ Update README          │ Docs     │ ● Open   │   │
│  └──────┴────────────────────────┴──────────┴──────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Recent Activity                                      │   │
│  │ ─────────────────────────────────────────────────────│   │
│  │ alice commented on T-42 "Added validation"           │   │
│  │ bob moved T-44 to Done                              │   │
│  │ alice created Epic: "API Documentation"              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Elements:**
- Stats cards with progress bars
- Assigned tasks table (sortable by status)
- Recent activity feed

---

## Page: Epics List

```
┌─────────────────────────────────────────────────────────────┐
│  Epics                                      [+ New Epic]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filter: [All Status ▼]  [Search...]                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Epic                  │ Tasks  │ Progress │ Status │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 📁 User Authentication│ 5/8    │ ████████░░ │ ● In Progress │   │
│  │   Implement login...  │        │           │          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 📁 API Documentation │ 3/3    │ ██████████ │ ● Done    │   │
│  │   REST API spec...   │        │           │          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 📁 Deployment       │ 2/10   │ ██░░░░░░░░ │ ● Open    │   │
│  │   CI/CD pipeline... │        │           │          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click row → Epic detail page
- Click title → Inline edit
- Status badge click → Dropdown to change

---

## Page: Epic Detail

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Epics                                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ User Authentication                          [Edit] │   │
│  │ Status: [● In Progress ▼]                           │   │
│  │ Created by alice · Created Jan 20, 2026              │   │
│  │                                                     │   │
│  │ Description:                                        │   │
│  │ Implement login and session management for the     │   │
│  │ application. Include OAuth support for GitHub.      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Tasks (5/8 complete)                         [+ Add Task] │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ T-40  Design login form          alice    ● Done  │   │
│  │ ☑ T-41  Implement auth API           bob      ● Done  │   │
│  │ ☐ T-42  Implement login form         ---      ● Open │   │
│  │ ☐ T-43  Add session management       bob    ● In Prog │   │
│  │ ☐ T-44  Write unit tests             alice    ● Open   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Delete Epic]                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Elements:**
- Inline editing for title, description
- Task list with checkboxes for status
- Progress automatically calculated from tasks

---

## Page: Tasks List

```
┌─────────────────────────────────────────────────────────────┐
│  Tasks                                          [+ New Task]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filter: [Status ▼] [Priority ▼] [Epic ▼] [Assignee ▼]     │
│  Search: [Search tasks...]                                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ID     │ Title          │ Epic       │ Assignee │Status││
│  ├─────────────────────────────────────────────────────┤   │
│  │ T-42   │ Login form     │ Auth       │ ---      │ ● Open││
│  │ T-43   │ Session mgmt   │ Auth       │ bob      │ ● In  ││
│  │ T-44   │ Unit tests     │ Auth       │ alice    │ ● Open││
│  │ T-51   │ Update README  │ Docs       │ alice    │ ● Review│
│  │ T-52   │ CI/CD setup    │ Deployment │ ---      │ ● Open│
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Showing 1-20 of 50  [<] [1] [2] [3] [>]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Multi-column sorting (click header)
- Bulk actions: Change status, assign
- Quick status change from row

---

## Page: Task Detail

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Tasks                                           │
│                                                             │
│  ┌───────────────────────────────────┐ ┌─────────────────┐ │
│  │ T-42: Implement login form       │ │ Attachments     │ │
│  │ Epic: User Authentication        │ │ ─────────────── │ │
│  │                                 │ │ 📎 mockup.png   │ │
│  │ Status: [● Open ▼]              │ │ 📎 wireframe.pdf │ │
│  │ Priority: [● High ▼]            │ │                  │ │
│  │ Assignee: [Select ▼]            │ │ [+ Add File]     │ │
│  │                                 │ │                  │ │
│  │ Description:                   │ │ Actions:         │ │
│  │ Create HTML form with          │ │ [Edit Task]      │ │
│  │ email and password fields.     │ │ [Delete Task]    │ │
│  │ Include validation feedback.   │ │                  │ │
│  │                                 │ │                  │ │
│  └───────────────────────────────────┘ └─────────────────┘ │
│                                                             │
│  Comments (3)                                  [+ Add Comment]│
│  ┌─────────────────────────────────────────────────────┐   │
│  │ bob · Jan 25, 2026                                  │   │
│  │ Started working on the HTML structure              │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ alice · Jan 26, 2026                                │   │
│  │ Looks good! Don't forget accessibility             │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ [Comment input...]              [Post]              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Layout:**
- Two-column: Main content (left), sidebar (right)
- Editable fields inline
- File upload drag-and-drop
- Comment thread with timestamps

---

## Page: Admin Users

```
┌─────────────────────────────────────────────────────────────┐
│  User Management                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [+ Add User]                         [Generate API Key]    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Username   │ Email          │ Role    │ Actions    │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ alice      │ alice@...      │ Admin   │ [Edit] [X] │   │
│  │ bob        │ bob@...        │ Member  │ [Edit] [X] │   │
│  │ charlie    │ charlie@...    │ Viewer  │ [Edit] [X] │   │
│  │ ci-bot     │ (API)          │ Auto    │ [Regen] [X]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  API Keys                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Name           │ Key (partial)      │ Created  │     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ GitHub Actions│ agw_sk_abc123...   │ Apr 22   │ [X] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- User CRUD operations
- Role assignment
- API key management (show once, regenerate)
- Disable/delete users

---

## Component: Status Badge

```
● Open       ● In Progress   ● Review       ● Blocked       ● Done
(gray)       (blue)          (yellow)        (red)           (green)
```

---

## Component: Priority Badge

```
● Low         ● Medium        ● High         ● Critical
(gray)        (blue)          (orange)        (red)
```

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| Desktop (>1024px) | Sidebar + Content |
| Tablet (768-1024px) | Collapsible sidebar |
| Mobile (<768px) | Bottom nav, full-width content |

---

## Open Questions for UI

1. **Dark mode?** - Preference or follow system?
2. **Notification bell?** - In-app notifications?
3. **Keyboard shortcuts?** - Common actions like 'n' for new task?
4. **Drag-drop reordering?** - Manual task ordering within epic?
