

**1. The Ledger**
*Query:*
```python
aggregates = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
    total_credit=Sum('amount_paise', filter=Q(type='CREDIT')),
    total_debit=Sum('amount_paise', filter=Q(type='DEBIT')),
    total_hold=Sum('amount_paise', filter=Q(type='HOLD')),
    total_release=Sum('amount_paise', filter=Q(type='RELEASE'))
)
available = credit - debit - hold + release
```
*Why:* I modeled it this way because keeping a hardcoded balance column is dangerus. If updating the balance fails but the ledger saves, the data gets totally corrupted. By just summing everything up on the fly, the ledger history is the only source of truth. The balance can never go out of sync.

**2. The Lock**
*Code:*
```python
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    # check balance and create payout
```
*Primitive:* It relys on **select_for_update()** Basically it locks that specific row in the Postgres database. If two payout request come at the exact same time for the same merchant, the database makes the second request wait in line until the first one is completely done.

**3. The Idempotency**
We store the key in the **IdempotencyKey** table linked to the merchant. When a request comes, we try to create that key. If the first request is still processing when the second arrives, the database will throw a unique constraint error (because the key is already in the table), so the second request gets rejected immediately. Once the first request finishes, we save its response so if they try again, we just give them the cached response.

**4. The State Machine**
*Where:* Inside `apps/payouts/models.py`.
*The check:*
```python
VALID_TRANSITIONS = {
    Status.PENDING: {Status.PROCESSING, Status.FAILED},
    Status.PROCESSING: {Status.COMPLETED, Status.FAILED},
    Status.COMPLETED: set(),
    Status.FAILED: set(),
}

def can_transition_to(self, new_status):
    return new_status in self.VALID_TRANSITIONS[self.status]
```
I used a dictionary to map what states can go where. **FAILED** maps to an empty set **set()**, meaning its a final state. It can't never transition anywhere else.

**5. The AI Audit**
*What it gave me:* At first, the AI tried to update the balance by just doing math in python:
```python
merchant.balance -= payout_amount
merchant.save()
```
*What I caught:* I realized this creates a massive race condition. If two requests happen at the same millisecond, they both read the old balance, subtract, and save, meaning one transaction completely overrides the other and money is lost.
*What I replaced it with:* I deleted the **balance**  column entirely from the Merchant model. Now I just calculate it dynamically using the **aggregate** sum function on the Ledger table (like in answer #1). No more race conditions!
