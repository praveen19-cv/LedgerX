import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings


class IdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    key = models.CharField(max_length=255, db_index=True)
    response_body = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "idempotency_key"
        unique_together = [("merchant", "key")]
        indexes = [
            models.Index(fields=["merchant", "key"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            expiry_hours = getattr(settings, "IDEMPOTENCY_KEY_EXPIRY_HOURS", 24)
            self.expires_at = timezone.now() + timedelta(hours=expiry_hours)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"IdempotencyKey({self.key}) for merchant {self.merchant_id}"
