"""
Tests for concurrency safety and idempotency.

Run: python manage.py test apps.tests
"""

import uuid
import threading
from django.test import TestCase, TransactionTestCase

from apps.merchants.models import Merchant, BankAccount
from apps.ledger.models import LedgerEntry
from apps.merchants.balance import get_balance_for_merchant
from apps.payouts.models import Payout
from apps.payouts.service import PayoutService, InsufficientFundsError


def _create_test_merchant(credit_paise=100_00):
    """Helper: create a merchant with initial credit balance."""
    merchant = Merchant.objects.create(
        name="Test Merchant", email=f"test-{uuid.uuid4()}@example.com"
    )
    bank = BankAccount.objects.create(
        merchant=merchant,
        account_number="1234567890",
        ifsc_code="HDFC0001234",
        account_holder_name="Test Merchant",
    )
    LedgerEntry.objects.create(
        merchant=merchant,
        type=LedgerEntry.EntryType.CREDIT,
        amount_paise=credit_paise,
        reference_type=LedgerEntry.ReferenceType.CREDIT,
        description="Initial test credit",
    )
    return merchant, bank


class BalanceCalculationTest(TestCase):
    """Unit tests for DB-level balance calculation."""

    def test_initial_credit_balance(self):
        merchant, _ = _create_test_merchant(credit_paise=10_000)
        self.assertEqual(get_balance_for_merchant(merchant.id), 10_000)

    def test_balance_after_hold(self):
        merchant, bank = _create_test_merchant(credit_paise=10_000)
        LedgerEntry.objects.create(
            merchant=merchant,
            type=LedgerEntry.EntryType.HOLD,
            amount_paise=3_000,
            reference_type=LedgerEntry.ReferenceType.PAYOUT,
            reference_id=uuid.uuid4(),
        )
        self.assertEqual(get_balance_for_merchant(merchant.id), 7_000)

    def test_balance_after_release(self):
        merchant, bank = _create_test_merchant(credit_paise=10_000)
        ref_id = uuid.uuid4()
        LedgerEntry.objects.create(
            merchant=merchant, type=LedgerEntry.EntryType.HOLD,
            amount_paise=3_000, reference_type=LedgerEntry.ReferenceType.PAYOUT,
            reference_id=ref_id,
        )
        LedgerEntry.objects.create(
            merchant=merchant, type=LedgerEntry.EntryType.RELEASE,
            amount_paise=3_000, reference_type=LedgerEntry.ReferenceType.PAYOUT,
            reference_id=ref_id,
        )
        # Hold + Release cancel out → back to full balance
        self.assertEqual(get_balance_for_merchant(merchant.id), 10_000)


class IdempotencyTest(TestCase):
    """Idempotency: same key must return same response, no duplicate payout."""

    def test_same_key_returns_cached_response(self):
        merchant, bank = _create_test_merchant(credit_paise=100_00)
        key = str(uuid.uuid4())

        _, created1, resp1 = PayoutService.create_payout(
            merchant.id, 50_00, bank.id, key
        )
        _, created2, resp2 = PayoutService.create_payout(
            merchant.id, 50_00, bank.id, key
        )

        self.assertTrue(created1)
        self.assertFalse(created2)  # duplicate → not created
        self.assertEqual(resp1["id"], resp2["id"])  # same payout
        self.assertEqual(Payout.objects.filter(merchant=merchant).count(), 1)

    def test_insufficient_funds_raises(self):
        merchant, bank = _create_test_merchant(credit_paise=50_00)
        with self.assertRaises(InsufficientFundsError):
            PayoutService.create_payout(
                merchant.id, 100_00, bank.id, str(uuid.uuid4())
            )


class ConcurrencyTest(TransactionTestCase):
    """
    Concurrency: two simultaneous requests for ₹60 with ₹100 balance.
    Only one must succeed. No overdraft.

    Uses TransactionTestCase so each thread has its own DB connection
    and the SELECT FOR UPDATE lock is exercised.
    """

    def setUp(self):
        self.merchant, self.bank = _create_test_merchant(credit_paise=100_00)

    def test_concurrent_payouts_no_overdraft(self):
        errors = []
        results = []

        def attempt_payout():
            try:
                _, created, resp = PayoutService.create_payout(
                    self.merchant.id, 60_00, self.bank.id, str(uuid.uuid4())
                )
                results.append(created)
            except InsufficientFundsError:
                results.append(False)
            except Exception as exc:
                errors.append(str(exc))

        t1 = threading.Thread(target=attempt_payout)
        t2 = threading.Thread(target=attempt_payout)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # Exactly one should succeed
        successful = [r for r in results if r is True]
        self.assertEqual(len(successful), 1, "Exactly one concurrent payout must succeed")

        # Balance must never go negative
        balance = get_balance_for_merchant(self.merchant.id)
        self.assertGreaterEqual(balance, 0, "Balance must never go negative")
