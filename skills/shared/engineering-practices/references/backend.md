# Backend practices

## Trace the business operation

Start from the HTTP request, message, or scheduled job. The entry point decodes the protocol and establishes the caller's identity. The operation applies authorization and business rules and decides what must commit together. Code that talks to a database or provider owns its query or protocol details. Small handlers can carry several of these responsibilities in one module. Separate them when another entry point needs the same operation or a dependency has a contract worth isolating.

Follow the transaction handle through every participating write. A helper that opens a new connection can commit work even if the calling operation rolls back. Carry tenant and resource scope through the actual read or write, including bulk paths.

## Bound list queries and related work

For a project inbox showing twenty projects and an unread count per project, first identify what determines membership and order. Apply the tenant, authorization, filter, and stable ordering before selecting the page. If counts are display-only, fetch or aggregate counts for the selected project IDs in bulk. If the list sorts by unread count, incorporate that count when ranking the candidates. Sorting only the selected page produces a different result.

Trace the **database calls and rows processed** as page size and total history grow. Reading a page and querying each project's count launches one additional query per project. Parallelizing those reads with `Promise.all` still consumes those calls and can exhaust the connection pool. A single join can also multiply rows or truncate parents when a limit applies to joined children. Choose a grouped read, a join, or a page followed by bounded batches according to the result shape and the database limits.

Exercise a sparse page and a full page in a tenant with substantial history. Observe query count, actual rows scanned, transferred fields, and the query plan on representative data. A fixed number of queries can still scan all messages in the tenant. For cursor pagination, include a tie breaker in the ordering and cursor. If the product requires a stable snapshot across pages while rows change, specify how it obtains one.

## Enforce concurrent writes at the data owner

Write the invariant in terms of committed state. For example, two successful reservations must never consume the same last item. For a single inventory row, a conditional decrement can require the correct tenant, item, and sufficient stock in the write predicate. Validate a positive quantity and check the affected row count. If creating the reservation is part of the same promise, insert its record in that transaction. Force the insert to fail and verify that the stock decrement rolls back.

Match the mechanism to the invariant. A unique constraint can protect a business key across service replicas. A version predicate can reject a stale edit. A rule involving several rows may require locking the relevant state or using a suitable isolation level and handling transaction conflicts. Check the actual database's guarantees. Keeping a read and write in one transaction alone does not specify what other transactions can do between them.

Keep transactions short. For a database operation coupled to a provider call, record enough durable state to recover if the provider succeeds and the local write fails. A local rollback cannot undo a completed remote request.

## Bound I/O and own its lifetime

Give each request, stream, and background job an owner for completion, failure, cancellation, and cleanup. A small fixed set of independent reads can run concurrently. For an input-driven batch, bound the number of operations started and the amount buffered, accounting for downstream capacity and other requests. Acquiring a permit after starting each operation leaves the expensive work unbounded.

Propagate cancellation to operations that support it. For a stream, stop pulling or apply backpressure when the reader slows down, and release the source on disconnect. For a non-cancellable operation, decide who handles a late result. Returning a timeout response can leave the work running.

Give retry responsibility to a specific layer with a bounded attempt or elapsed-time budget. Treat a lost response to a write as an unknown outcome. Resolve it with the provider's idempotency contract, an operation lookup, or reconciliation before repeating an effect. Persist a background task before promising work that must survive process exit.

## Accept webhooks and recover message processing

For a credit event, define the idempotency key's scope and which accepted business fields must match on replay. For example, within one partner's event namespace, repeating event 42 for the same account and amount should return the recorded outcome. Reusing 42 with a different amount should surface a conflict. Compare the normalized business fields. Delivery timestamps and transport metadata may legitimately differ between attempts.

Authenticate inbound events according to the provider contract before accepting their identity or applying a business effect. In the database, make the key unique in its intended scope and commit the processed record together with the ledger effect. When concurrent attempts collide, use the committed outcome and verify its payload according to the contract. A preliminary lookup is useful for a common replay but cannot by itself arbitrate two first deliveries.

| Interruption | Design and recovery |
| --- | --- |
| Business data commits, then the process exits before publishing a required event | Commit a durable publication intent with the data, such as an outbox row. Give a dispatcher responsibility for pending and failed sends. |
| A dispatcher publishes, then exits before marking the event sent | Reuse the event identity on the next attempt and make consumption safe on replay. |
| A consumer commits the effect, then loses its delivery before acknowledging it | On redelivery, find the committed outcome. Acknowledge after the effect commits or a durable handoff takes responsibility for it. |
| A provider performs an action, then its response is lost | Recover with the same provider key within its retention window, or query and reconcile the outcome before issuing another action. |
| A worker's lease expires while its work is in progress | Condition the result write on the current lease generation or version so the old worker cannot overwrite a new result. Protect external effects separately. |

Publisher confirmation and consumer acknowledgement cover different steps. For a webhook, choose the success response point based on what the receiver promises to take responsibility for. For a disposable notification, a best-effort send can be enough. Introduce a durable handoff when losing that work would violate the contract.

Classify retryable failures, business rejections, and malformed messages. Make exhausted attempts inspectable and recoverable, with a stable operation ID, stage, and attempt history. When ordering matters, identify the entity that requires it and specify what happens when an older event arrives late.

Verify duplicate and conflicting payloads, two simultaneous first attempts, and a restart between commit and acknowledgement. Assert the resulting ledger entries and the caller's outcome. Broker delivery counts can legitimately vary across these scenarios.

## Set cache and migration contracts

For a cache, identify the authoritative read, authorized key scope, maximum acceptable staleness, and invalidation paths. Include capacity limits and the fallback when the cache is unavailable. Avoid stale cached values in decisions that require current transactional data.

Walk through an overlapping read and write. Read A obtains version 7, write B commits version 8 and invalidates the cache, then A tries to cache version 7. For a strict freshness requirement, make the outdated fill fail, for example by preserving a generation across invalidation and comparing it atomically at fill time. If the application tolerates staleness, establish how long the value can actually persist, including a late fill that restarts its TTL. Test this ordering using explicit coordination between A and B.

Plan storage and message changes around the readers and writers that can coexist during rollout. For a newly required field, identify how old rows will be read, when old writers stop creating them, and when enforcement becomes safe. Check lock duration, backfill size, and how an interrupted migration resumes. Verify old and new formats across the actual deployment window.
