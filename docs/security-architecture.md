# Novera — Enterprise Security & Multi-Tenant Authorization Architecture

## 1. Core Principles
1. **Zero Trust Server-Side Enforcement**: Identity and tenancy are derived solely from cryptographically signed JWT credentials. Request body fields such as `account_id`, `workspace_id`, or `user_id` are never trusted for authorization.
2. **Strict Multi-Tenant Isolation**: Company A must never observe Company B's datasets, schemas, reports, analytics, AI summaries, conversations, activities, or audit logs.
3. **IDOR Defense**: All resource retrieval, mutation, and deletion operations evaluate ownership prior to execution.
4. **Separation of Audit & Activity**: Compliance-grade immutable audit logs are isolated from end-user product activity feeds.

---

## 2. Tenancy Hierarchy
```
ACCOUNT / ORGANIZATION (e.g., acc_...)
         │
         ├── WORKSPACE (e.g., default, ws_operations)
         │        │
         │        ├── WORKSPACE MEMBERS (User + Role)
         │        │
         │        ├── DATASETS (Versions, Schemas, Knowledge)
         │        │
         │        ├── PROCESSING JOBS
         │        │
         │        ├── REPORTS (Snapshots, Summaries, Evidence)
         │        │
         │        ├── ANALYST SESSIONS (Messages, Plans)
         │        │
         │        └── ACTIVITIES
         │
         └── COMPLIANCE AUDIT LOGS (Account-level Immutable History)
```

---

## 3. Authorization Flow & Scoping
Every protected FastAPI endpoint injects `AuthorizedScope` via `get_authorized_scope`:

```python
@dataclass(frozen=True)
class AuthorizedScope:
    user_id: str
    account_id: str
    workspace_id: str
    role: str
    email: str
```

### 3.1 Scoped MongoDB Repositories
Every repository query mandates `account_id`:
```python
# CORRECT: Multi-tenant scoped query
self.collection.find_one({"dataset_id": dataset_id, "account_id": scope.account_id})

# FORBIDDEN: Unscoped query allowing IDOR
self.collection.find_one({"dataset_id": dataset_id})
```

---

## 4. Role-Based Access Control (RBAC)
Novera implements centralized role permission evaluation (`app.core.permissions`):

| Permission | Owner | Admin | Analyst | Member |
| :--- | :---: | :---: | :---: | :---: |
| `workspace.read` |  |  |  |  |
| `workspace.manage` |  | ❌ | ❌ | ❌ |
| `dataset.read` |  |  |  |  |
| `dataset.create` |  |  |  | ❌ |
| `dataset.update` |  |  | ❌ | ❌ |
| `dataset.delete` |  |  | ❌ | ❌ |
| `report.read` |  |  |  |  |
| `report.create` |  |  |  | ❌ |
| `report.delete` |  |  | ❌ | ❌ |
| `analytics.run` |  |  |  | ❌ |
| `mapping.update` |  |  | ❌ | ❌ |
| `analyst.use` |  |  |  |  |
| `audit.read` |  |  | ❌ | ❌ |
| `users.manage` |  |  | ❌ | ❌ |

---

## 5. Cache Isolation & Logout Clearing
1. **Frontend TanStack Query**:
   - Query keys are strictly scoped with tenant identity:
     `['dashboard-stats', user?.id]`
     `['dashboard-reports', user?.id]`
     `['dataset', accountId, datasetId]`
2. **Session Termination**:
   - Upon logout, `queryClient.clear()` and `localStorage.clear()` wipe all in-memory and persisted query caches.
   - Prevents residual data from Company A flashing when Company B logs in on the same workstation.

---

## 6. AI Data Boundary & Grounding Protection
1. **No Raw Model Access**: External LLMs never possess direct MongoDB access or unconstrained query privileges.
2. **Verified Evidence Filter**: Before prompt construction, dataset and report scopes are verified against the active `account_id`. Only deterministic, aggregated evidence is supplied.
3. **Verification & Claims**: All AI-generated claims must be grounded against deterministic analytics engine outputs. Unverified claims are rejected or flagged.
