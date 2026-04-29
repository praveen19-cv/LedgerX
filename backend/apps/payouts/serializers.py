from rest_framework import serializers
from .models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    amount_rupees = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    bank_account_number = serializers.CharField(
        source="bank_account.account_number", read_only=True
    )

    class Meta:
        model = Payout
        fields = [
            "id",
            "merchant_id",
            "bank_account_id",
            "bank_account_number",
            "amount_paise",
            "amount_rupees",
            "status",
            "status_display",
            "idempotency_key",
            "retry_count",
            "failure_reason",
            "processing_started_at",
            "created_at",
            "updated_at",
        ]

    def get_amount_rupees(self, obj):
        return round(obj.amount_paise / 100, 2)


class CreatePayoutSerializer(serializers.Serializer):
    merchant_id = serializers.UUIDField()
    bank_account_id = serializers.UUIDField()
    amount_paise = serializers.IntegerField(min_value=1)
