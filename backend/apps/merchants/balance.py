from django.db import models
from django.db.models import Sum, Case, When, Value, IntegerField


def get_balance_for_merchant(merchant_id):
    """
    Compute balance purely at DB level — no Python arithmetic on money.

    Balance = SUM(CREDIT + RELEASE) - SUM(DEBIT + HOLD)

    Returns balance in paise (integer).
    """
    from apps.ledger.models import LedgerEntry

    result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        balance=Sum(
            Case(
                When(type__in=["CREDIT", "RELEASE"], then="amount_paise"),
                When(type__in=["DEBIT", "HOLD"], then=models.F("amount_paise") * -1),
                output_field=models.BigIntegerField(),
            )
        )
    )
    return result["balance"] or 0


def get_held_balance_for_merchant(merchant_id):
    """Returns total amount currently on HOLD (reserved but not yet debited)."""
    from apps.ledger.models import LedgerEntry

    result = LedgerEntry.objects.filter(
        merchant_id=merchant_id,
        type="HOLD",
    ).aggregate(total=Sum("amount_paise"))
    return result["total"] or 0
