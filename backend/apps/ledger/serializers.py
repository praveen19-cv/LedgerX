from rest_framework import serializers
from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    amount_rupees = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "merchant_id",
            "type",
            "type_display",
            "amount_paise",
            "amount_rupees",
            "reference_type",
            "reference_id",
            "description",
            "created_at",
        ]

    def get_amount_rupees(self, obj):
        return round(obj.amount_paise / 100, 2)
