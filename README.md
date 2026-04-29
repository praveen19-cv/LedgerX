# LedgerX — Payout Engine

> A production-minded, cross-border payment settlement simulation.
> Built with Django + DRF · Celery + Redis · PostgreSQL · React + Tailwind.

---

## Project Structure

```
LedgerX/
├── backend/                   # Django API + Celery workers
│   ├── ledgerx/               # Django project (settings, urls, celery)
│   ├── apps/
│   │   ├── merchants/         # Merchant model, bank accounts, balance utilities
│   │   ├── ledger/            # LedgerEntry model (CREDIT/DEBIT/HOLD/RELEASE)
│   │   ├── payouts/           # Payout model, PayoutService, Celery tasks
│   │   ├── idempotency/       # IdempotencyKey model
│   │   ├── core/              # Shared exception handler
│   │   └── tests/             # Concurrency + idempotency tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                  # React 18 + Vite + Tailwind
│   ├── src/
│   │   ├── api/               # Typed API client
│   │   ├── components/        # BalanceCards, PayoutForm, PayoutTable, LedgerTable
│   │   ├── hooks/             # useBalance, usePayouts, useLedger (polling)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml         # Full stack: DB + Redis + API + Worker + Beat + Frontend
├── EXPLAINER.md               # Engineering decisions deep-dive
└── README.md
```

---

## Quick Start (Docker)

```bash
# Clone and start everything
docker-compose up --build

# In another terminal, run tests
docker-compose exec backend python manage.py test apps.tests
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/

---

## Quick Start (Local Development)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Copy env
copy .env.example .env       # Edit DATABASE_URL and REDIS_URL

python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

### Celery Worker (new terminal)

```bash
cd backend
celery -A ledgerx worker --loglevel=info
```

### Celery Beat (new terminal)

```bash
cd backend
celery -A ledgerx beat --loglevel=info
```

### Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/merchants/` | List all merchants |
| GET | `/api/v1/merchants/<id>/balance/` | Available + held balance |
| GET | `/api/v1/merchants/<id>/ledger/` | Paginated ledger |
| POST | `/api/v1/payouts/` | Create payout (requires `Idempotency-Key` header) |
| GET | `/api/v1/payouts/?merchant_id=<id>` | Payout history |
| GET | `/api/v1/payouts/<id>/` | Single payout status |

### Create Payout Example

```bash
curl -X POST http://localhost:8000/api/v1/payouts/ \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(python -c 'import uuid; print(uuid.uuid4())')" \
  -d '{
    "merchant_id": "<uuid>",
    "bank_account_id": "<uuid>",
    "amount_paise": 50000
  }'
```

---

## Key Engineering Decisions

See [EXPLAINER.md](./EXPLAINER.md) for full rationale. Summary:

| Decision | Why |
|----------|-----|
| No `balance` column | DB-level aggregation = single source of truth |
| Paise (integers) | No floating-point rounding errors |
| `SELECT FOR UPDATE` | Row-level lock prevents overdraft in concurrent requests |
| HOLD → DEBIT → RELEASE pattern | Correct bookkeeping for in-flight payouts |
| Idempotency keys | Safe retries — no duplicate payouts on network failure |
| `TransactionTestCase` for concurrency tests | Allows real lock contention between threads |

---

## Running Tests

```bash
cd backend
python manage.py test apps.tests --verbosity=2
```

Tests cover:
- ✅ Balance calculation correctness
- ✅ Idempotency (same key → same response, no duplicate payout)
- ✅ Concurrent overdraft prevention (two threads, one winner)
