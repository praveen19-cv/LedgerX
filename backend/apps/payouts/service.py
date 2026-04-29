"""
Payout Service — The heart of LedgerX.

All payout creation logic lives here. The service:
  1. Checks idempotency (returns cached response if duplicate key).
  2. Acquires a row-level lock on the merchant (SELECT FOR UPDATE).
  3. Calculates available balance at DB level — no Python float math.
  4. Creates the Payout + LedgerEntry(HOLD) atomically.
  5. Stores the idempotency record.

This is the only correct way to create a payout — views call this,
never write directly to the Payout model.
"""

import logging
from django.db import transaction
from django.utils import timezone

from apps.merchants.models import Merchant, BankAccount
from apps.merchants.balance import get_balance_for_merchant
from apps.ledger.models import LedgerEntry
from apps.idempotency.models import IdempotencyKey
from .models import Payout

logger = logging.getLogger(__name__)


class InsufficientFundsError(Exception):
    pass


class InvalidRequestError(Exception):
    pass


class PayoutService:

    @staticmethod
    def create_payout(merchant_id, amount_paise, bank_account_id, idempotency_key_str):
        """
        Idempotency-safe, concurrency-safe payout creation.

        Returns (payout, created, cached_response):
          - payout: Payout instance
          - created: bool — True if new, False if duplicate key
          - cached_response: stored response body if duplicate
        """
        # ── Step 1: Check idempotency ──────────────────────────────────────────
        try:
            existing_key = IdempotencyKey.objects.get(
                merchant_id=merchant_id,
                key=idempotency_key_str,
            )
            if not existing_key.is_expired:
                logger.info(
                    "Idempotency hit for key=%s merchant=%s",
                    idempotency_key_str,
                    merchant_id,
                )
                return None, False, existing_key.response_body
        except IdempotencyKey.DoesNotExist:
            pass

        # ── Step 2: Transactional creation with row-level locking ──────────────
        with transaction.atomic():
            # Lock the merchant row to prevent concurrent payout creation.
            # Only one transaction can hold this lock at a time.
            try:
                merchant = Merchant.objects.select_for_update().get(id=merchant_id)
            except Merchant.DoesNotExist:
                raise InvalidRequestError(f"Merchant {merchant_id} not found")

            try:
                bank_account = BankAccount.objects.get(
                    id=bank_account_id, merchant=merchant
                )
            except BankAccount.DoesNotExist:
                raise InvalidRequestError("Bank account not found or not owned by merchant")

            # ── Step 3: Validate amount ────────────────────────────────────────
            if amount_paise <= 0:
                raise InvalidRequestError("Amount must be positive")

            # ── Step 4: Calculate available balance at DB level ───────────────
            available_balance = get_balance_for_merchant(merchant_id)

            if available_balance < amount_paise:
                raise InsufficientFundsError(
                    f"Insufficient funds: available={available_balance} paise, "
                    f"requested={amount_paise} paise"
                )

            # ── Step 5: Create Payout (PENDING) + LedgerEntry (HOLD) ─────────
            payout = Payout.objects.create(
                merchant=merchant,
                bank_account=bank_account,
                amount_paise=amount_paise,
                status=Payout.Status.PENDING,
                idempotency_key=idempotency_key_str,
            )

            LedgerEntry.objects.create(
                merchant=merchant,
                type=LedgerEntry.EntryType.HOLD,
                amount_paise=amount_paise,
                reference_type=LedgerEntry.ReferenceType.PAYOUT,
                reference_id=payout.id,
                description=f"Hold for payout {payout.id}",
            )

            # ── Step 6: Store idempotency record ──────────────────────────────
            response_body = {
                "id": str(payout.id),
                "merchant_id": str(merchant.id),
                "amount_paise": amount_paise,
                "amount_rupees": amount_paise / 100,
                "status": payout.status,
                "bank_account_id": str(bank_account.id),
                "created_at": payout.created_at.isoformat(),
            }
            IdempotencyKey.objects.get_or_create(
                merchant=merchant,
                key=idempotency_key_str,
                defaults={
                    "response_body": response_body,
                    "status_code": 201,
                },
            )

            logger.info(
                "Payout created: id=%s merchant=%s amount=%s",
                payout.id,
                merchant_id,
                amount_paise,
            )
            return payout, True, response_body
