# LedgerX EXPLAINER — Engineering Decisions

> This document answers the "why" behind every major design decision in LedgerX.
> Written for evaluators who want to see engineering judgment, not just code.

---

## 1. Why PostgreSQL and not SQLite?

SQLite doesn't support `SELECT FOR UPDATE` (row-level locking) or true concurrent writers.
LedgerX requires strict concurrency guarantees — two simultaneous payout requests must
be serialized at the database level. PostgreSQL's MVCC + row-locking is the only correct tool.

---

## 2. Why no `balance` column on the Merchant table?

Storing a `balance` field creates a dual-write problem:
- You must update two places atomically (balance + ledger entry).
- On failure, you risk an inconsistency that's invisible until an audit.

Instead, LedgerX computes balance **on the fly** via a SQL aggregation:

```sql
SELECT COALESCE(SUM(
  CASE
    WHEN type IN ('CREDIT', 'RELEASE') THEN amount_paise
    WHEN type IN ('DEBIT', 'HOLD') THEN -amount_paise
  END
), 0) AS balance
FROM ledger_entry
WHERE merchant_id = %s;
```

**Single source of truth = the ledger itself.** This is how double-entry bookkeeping works.

---

## 3. Why paise (integers) and not rupees (floats)?

`0.1 + 0.2 != 0.3` in IEEE 754 floating point. Money maths using floats will silently
accumulate rounding errors. LedgerX stores everything in **paise (smallest indivisible unit)**
as `BigInteger`. All arithmetic is exact. Conversion to rupees happens only at the display layer.

> This mirrors how Stripe, Razorpay, and all serious payment APIs work.

---

## 4. How does concurrency safety work?

Two workers payout ₹60 from a ₹100 balance simultaneously:

```
Worker A          Worker B
─────────         ─────────
SELECT ... FOR UPDATE (acquires row lock on merchant)
                  SELECT ... FOR UPDATE (BLOCKS — waits for A)
calculate balance = ₹100 ✓
create payout, HOLD ₹60
COMMIT
                  (lock released — Worker B continues)
                  calculate balance = ₹40 ✗ (60 > 40)
                  raise InsufficientFundsError
```

**Only one transaction can check-and-hold at a time.** No race. No overdraft.

The lock acquisition is in `apps/payouts/service.py`:
```python
merchant = Merchant.objects.select_for_update().get(id=merchant_id)
```

---

## 5. Why idempotency keys?

Network failures are real. A client may retry a payout request not knowing if the first arrived.
Without idempotency, you'd create two payouts.

LedgerX implements server-side idempotency:
1. Client sends `Idempotency-Key: <UUID>` header.
2. On first request: process normally, store the response body against the key.
3. On subsequent requests with the same key: return the **stored response** — no new payout created.
4. Keys expire after 24 hours (configurable).

The key is scoped **per merchant**, so two merchants can use the same UUID without collision.

---

## 6. Why HOLD + DEBIT instead of directly debiting?

A payout takes time. Between submission and settlement:
- Funds must be **reserved** (not double-spendable).
- But they shouldn't be permanently removed until the bank confirms.

```
PENDING  → HOLD entry (funds reserved)
COMPLETED → DEBIT entry (funds permanently gone)
FAILED   → RELEASE entry (funds returned)
```

This means the balance formula always reflects the true economic picture even for in-flight payouts.

---

## 7. How does the payout state machine work?

```
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED
```

**Terminal states** (COMPLETED, FAILED) cannot transition further.
Every transition is validated in `Payout.can_transition_to()` before any DB write happens.

```python
def can_transition_to(self, new_status):
    return new_status in self.VALID_TRANSITIONS.get(self.status, [])
```

In the Celery worker, all state changes also re-acquire `SELECT FOR UPDATE` to prevent
concurrent workers from transitioning the same payout.

---

## 8. What happens to stuck payouts?

The `recover_stuck_payouts` beat task runs every 30 seconds. Any payout stuck in
`PROCESSING` beyond the threshold (default: 30 seconds) is treated as a timeout.

- **Retry count < 3**: Transition back to PENDING. Celery will reprocess.
- **Backoff**: Wait = 2^retry_count seconds before re-queuing.
- **Exhausted**: Mark FAILED, insert RELEASE entry to refund merchant.

---

## 9. What does `skip_locked=True` do in the Celery worker?

When multiple Celery workers are running, they'll all try to pick up PENDING payouts.
`select_for_update(skip_locked=True)` tells each worker to skip rows that another
worker already has a lock on — preventing duplicate processing without errors.

---

## 10. Why Celery Beat for scheduling?

Two scheduled tasks:
1. `process_pending_payouts` — every 10 seconds: picks up PENDING, starts processing.
2. `recover_stuck_payouts` — every 30 seconds: watchdog for stuck PROCESSING payouts.

Beat is the Django-aware cron alternative. It doesn't require a separate cron daemon and
integrates with the same Celery broker, making it trivial to deploy.

---

## 11. Frontend polling strategy

The React frontend polls the API every **5 seconds** using `setInterval` inside custom hooks (`useBalance`, `usePayouts`). This is intentional:
- No WebSocket complexity for an MVP.
- Sufficient latency for a monitoring dashboard.
- Easy to swap for WebSocket in v2.

---

## 12. Testing strategy rationale

| Test Type | Class | Why |
|-----------|-------|-----|
| Unit | `BalanceCalculationTest` (TestCase) | Fast, isolated balance math |
| Unit | `IdempotencyTest` (TestCase) | DB constraint validation |
| Integration | `ConcurrencyTest` (TransactionTestCase) | Real row-level locks; `TestCase` wraps in a transaction which prevents `SELECT FOR UPDATE` from working across threads |

**Key insight**: `TestCase` wraps each test in a transaction, which makes it impossible to test actual row locking. `TransactionTestCase` commits each operation for real, so the lock contention actually fires.
