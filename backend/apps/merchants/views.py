from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Merchant
from .serializers import MerchantSerializer
from .balance import get_balance_for_merchant, get_held_balance_for_merchant


class MerchantListView(APIView):
    """GET /api/v1/merchants — list all merchants (dev/demo convenience)."""

    def get(self, request):
        merchants = Merchant.objects.all()
        serializer = MerchantSerializer(merchants, many=True)
        return Response({"success": True, "data": serializer.data})


class MerchantBalanceView(APIView):
    """
    GET /api/v1/merchants/<merchant_id>/balance
    Returns available and held balances in both paise and rupees.
    """

    def get(self, request, merchant_id):
        try:
            merchant = Merchant.objects.get(id=merchant_id)
        except (Merchant.DoesNotExist, ValueError):
            return Response(
                {"success": False, "error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        available_paise = get_balance_for_merchant(merchant_id)
        held_paise = get_held_balance_for_merchant(merchant_id)

        return Response(
            {
                "success": True,
                "data": {
                    "merchant_id": str(merchant.id),
                    "merchant_name": merchant.name,
                    "available_paise": available_paise,
                    "available_rupees": available_paise / 100,
                    "held_paise": held_paise,
                    "held_rupees": held_paise / 100,
                },
            }
        )
