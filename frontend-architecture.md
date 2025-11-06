# Frontend Architecture Diagrams

This file contains the high-level component structure diagrams for the two frontend applications, including their backend connections and the human-computer collaboration workflow.

## 1. `archon-ui-main` (Admin UI) Component & API Structure

This diagram shows how the main pages of the Admin UI are composed of different feature views, and how these views interact with the `archon-server` backend.

```mermaid
graph TD
    subgraph Frontend: archon-ui-main
        subgraph Pages
            A[App.tsx]
            P1[KnowledgeBasePage]
            P2[ProjectPage]
            P3[MCPPage]
            P4[SettingsPage]
        end

        subgraph Feature Views
            V1[KnowledgeView]
            V2[ProjectsView]
            V3[McpView]
            V4[Settings Sections]
        end
    end

    subgraph Backend
        B1[archon-server]
    end

    A --> P1 & P2 & P3 & P4

    P1 --> V1
    P2 --> V2
    P3 --> V3
    P4 --> V4

    V1 -- GET /api/knowledge-items --> B1
    V2 -- GET /api/projects --> B1
    V2 -- GET /api/tasks --> B1
    V3 -- GET /api/mcp/status --> B1
    V4 -- GET /api/credentials --> B1
    V4 -- POST /api/credentials --> B1
```

## 2. `enduser-ui-fe` (End-User UI) Architecture & Workflow

This section contains two diagrams:
1.  A **Component Structure Diagram** showing the internal page and component composition.
2.  A **Human-Computer Collaboration Workflow** diagram illustrating the core interaction loop from task creation to AI completion.

### 2.1 Component Structure

```mermaid
graph TD
    subgraph Pages
        LP[LandingPage]
        AP[AuthPage]
        DP[DashboardPage]
        BP[BlogPage]
        SP[SettingsPage]
        AdP[AdminPage]
    end

    subgraph Dashboard Views
        V1[ListView]
        V2[TableView]
        V3[KanbanView]
        V4[GanttView]
    end

    subgraph Modals & Common Components
        M1[TaskModal]
        M2[ProjectModal]
        CC1[UserAvatar]
    end

    subgraph Backend
        B1[archon-server]
    end

    DP --> V1 & V2 & V3 & V4
    DP --> M1 & M2
    DP -- GET /api/tasks --> B1
    DP -- GET /api/projects --> B1

    AdP -- GET /api/employees --> B1
    BP -- GET /api/blogs --> B1
    SP -- POST /api/users/update --> B1
    AP -- POST /api/auth/login --> B1

    M1 -- POST /api/tasks --> B1
    M2 -- POST /api/projects --> B1
```

### 2.2 Human-Computer Collaboration Workflow (Phase 3.8)

This diagram illustrates the core concept of human-computer collaboration using dotted lines to represent the sequence of events.

```mermaid
graph TD
    subgraph User Interface: enduser-ui-fe
        U[User]
        D[DashboardPage]
        M[TaskModal]
    end

    subgraph Backend Services
        S[archon-server]
        A[AI Agent]
    end

    subgraph External Systems
        DB[Supabase DB]
        ST[Supabase Storage]
    end

    U -- 1. Creates/Assigns Task --> D
    D -- 2. Opens --> M
    M -- 3. `POST /api/tasks` --> S

    S -- 4. Updates task status --> DB
    S -- 5. Triggers Agent (async) --> A
    S -. "6. Broadcasts update (Socket.IO)" .-> D

    A -- 7. Executes task (e.g., research) --> A
    A -- 8. `POST /api/files/upload` --> S

    S -- 9. Uploads file to --> ST
    ST -- 10. Returns URL --> S
    S -- 11. Updates task with attachment URL --> DB

    DB -. "12. Notifies via DB changes" .-> S
    S -. "13. Broadcasts final update (Socket.IO)" .-> D

    D -- 14. Displays final result --> U
```
