import uuid
from django.db import models


class LedgerEntry(models.Model):

    class EntryType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"       # Money added to merchant
        DEBIT = "DEBIT", "Debit"          # Money taken (payout completed)
        HOLD = "HOLD", "Hold"             # Funds reserved for pending payout
        RELEASE = "RELEASE", "Release"   # Refund on payout failure

    class ReferenceType(models.TextChoices):
        PAYOUT = "PAYOUT", "Payout"
        CREDIT = "CREDIT", "Credit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        db_index=True,
    )
    type = models.CharField(max_length=10, choices=EntryType.choices)
    amount_paise = models.BigIntegerField()
    reference_type = models.CharField(
        max_length=10, choices=ReferenceType.choices, null=True, blank=True
    )
    reference_id = models.UUIDField(null=True, blank=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "ledger_entry"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "type"]),
            models.Index(fields=["merchant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.type} ₹{self.amount_paise / 100:.2f} for {self.merchant_id}"

    @property
    def amount_rupees(self):
        return self.amount_paise / 100
