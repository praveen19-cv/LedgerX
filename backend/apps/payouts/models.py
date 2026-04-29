import uuid
from django.db import models


class Payout(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    # Allowed state machine transitions
    VALID_TRANSITIONS = {
        Status.PENDING: [Status.PROCESSING],
        Status.PROCESSING: [Status.COMPLETED, Status.FAILED],
        Status.COMPLETED: [],  # Terminal state
        Status.FAILED: [],     # Terminal state
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.PROTECT,
        related_name="payouts",
        db_index=True,
    )
    bank_account = models.ForeignKey(
        "merchants.BankAccount",
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    amount_paise = models.BigIntegerField()
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    idempotency_key = models.CharField(max_length=255, db_index=True)
    retry_count = models.IntegerField(default=0)
    failure_reason = models.TextField(blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payout"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Payout {self.id} — {self.status} — ₹{self.amount_paise / 100:.2f}"

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def amount_rupees(self):
        return self.amount_paise / 100
