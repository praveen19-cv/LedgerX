from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.merchants.models import Merchant
from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


class LedgerListView(APIView):
    """
    GET /api/v1/merchants/<merchant_id>/ledger
    Returns paginated ledger for a merchant, latest-first.
    """

    def get(self, request, merchant_id):
        try:
            merchant = Merchant.objects.get(id=merchant_id)
        except (Merchant.DoesNotExist, ValueError):
            return Response(
                {"success": False, "error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        page_size = int(request.query_params.get("page_size", 20))
        page = int(request.query_params.get("page", 1))
        offset = (page - 1) * page_size

        entries = LedgerEntry.objects.filter(merchant=merchant).order_by("-created_at")
        total = entries.count()
        paginated = entries[offset : offset + page_size]
        serializer = LedgerEntrySerializer(paginated, many=True)

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size,
                },
            }
        )
