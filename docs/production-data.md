# Novera — Production Data, Persistence & Recovery Architecture

## 1. Executive Summary
Novera is a multi-tenant business intelligence and data processing SaaS platform. This document defines the production data storage topology, persistence guarantees, backup and restore runbooks, recovery point and time objectives (RPO/RTO), and retention lifecycle.

---

## 2. Infrastructure Topology

### 2.1 MongoDB Cluster Topology
- **Primary Database Engine**: MongoDB 6.0+ Replica Set (3-node minimum: Primary, Secondary, Secondary/Arbiter).
- **Driver**: PyMongo with connection pooling (`minPoolSize=10`, `maxPoolSize=100`, `serverSelectionTimeoutMS=4000`, `connectTimeoutMS=4000`).
- **Connection Management**: Centralized singleton client managed in `app.db.database`. Direct request-level client creation is strictly forbidden.
- **Failover**: Automatic primary election supported transparently by replica set replica URLs (`mongodb://node1,node2,node3/?replicaSet=rs0`).

### 2.2 File & Blob Storage Layer
- **Abstraction**: `StorageService` interface separating metadata from binary payloads.
- **Development**: Local isolated volume (`storage/uploads/{account_id}/`).
- **Production**: S3-compatible object store (AWS S3, Cloudflare R2, MinIO) with private bucket ACLs and server-side encryption (SSE-S3/KMS).
- **Access Control**: Pre-signed URLs or streaming through authenticated FastAPI endpoints verifying `account_id` and `workspace_id`. Raw storage credentials are never exposed to clients.

---

## 3. Data Lifecycle & Retention Strategy

| Lifecycle State | Description | Persistence Action | Retention Period |
| :--- | :--- | :--- | :--- |
| **ACTIVE** | Operational datasets, reports, analytics, sessions. | Persisted in primary collections with active indexes. | Indefinite / customer subscription duration. |
| **ARCHIVED** | Deprecated dataset versions or superseded reports. | Retained in version collections (`dataset_versions`, `report_versions`). Omitted from primary dashboard queries. | 365 days (configurable per enterprise SLA). |
| **DELETED (Soft)** | User-requested deletion. Resource flagged as deleted with UTC timestamp. | Hidden from standard list/query APIs; lineage references retained for historical reporting. | 90-day recovery grace period. |
| **PURGED (Hard)** | Cryptographic/permanent wipe of blobs and associated documents. | Hard delete from disk/S3 and MongoDB document removal upon explicit compliance request (GDPR/SOC2). | Immediately following expiration of grace period. |

---

## 4. Disaster Recovery & Target Metrics

- **Recovery Point Objective (RPO)**:
  - Target: **< 15 minutes**.
  - Mechanism: MongoDB continuous oplog streaming + daily full automated snapshots.
- **Recovery Time Objective (RTO)**:
  - Target: **< 1 hour**.
  - Mechanism: Automated cluster re-provisioning via Terraform/Kubernetes manifests and Point-in-Time (PITR) restore.

---

## 5. Backup & Restore Runbook

### 5.1 Automated Scheduled Backups
```bash
# Snapshot all collections using mongodump with oplog
mongodump --uri="$MONGODB_URI" --oplog --gzip --archive=/backups/novera_$(date +%Y%m%d_%H%M%S).gz
```

### 5.2 Verification & Validation
- Daily automated test-restore to an isolated staging environment.
- Verification script executes:
  - Schema integrity checks.
  - Multi-tenant boundary checks (ensuring cross-tenant records are strictly isolated).
  - Row count consistency against dataset metadata records.

### 5.3 Point-in-Time Restore (PITR)
```bash
# Restore specific point-in-time
mongorestore --uri="$TARGET_MONGODB_URI" --oplogReplay --gzip --archive=/backups/novera_snapshot.gz
```

---

## 6. Zero Cross-Tenant Leakage Verification
All database restoration and query routines enforce `account_id` and `workspace_id`. Even in multi-tenant environments sharing a single database replica set, tenant boundaries are enforced at the repository and aggregation layers.
