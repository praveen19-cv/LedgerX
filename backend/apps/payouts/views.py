import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.merchants.models import Merchant
from .models import Payout
from .serializers import PayoutSerializer, CreatePayoutSerializer
from .service import PayoutService, InsufficientFundsError, InvalidRequestError

logger = logging.getLogger(__name__)


class PayoutListCreateView(APIView):
    """
    GET  /api/v1/payouts?merchant_id=<uuid>   — Payout history
    POST /api/v1/payouts                       — Create payout (idempotency-safe)

    POST requires header:  Idempotency-Key: <unique-uuid>
    """

    def get(self, request):
        merchant_id = request.query_params.get("merchant_id")
        if not merchant_id:
            return Response(
                {"success": False, "error": "merchant_id query param required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payouts = Payout.objects.filter(merchant_id=merchant_id).select_related(
            "bank_account"
        )
        serializer = PayoutSerializer(payouts, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        # ── Validate idempotency header ────────────────────────────────────────
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"success": False, "error": "Idempotency-Key header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Validate request body ──────────────────────────────────────────────
        serializer = CreatePayoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            payout, created, response_body = PayoutService.create_payout(
                merchant_id=data["merchant_id"],
                amount_paise=data["amount_paise"],
                bank_account_id=data["bank_account_id"],
                idempotency_key_str=idempotency_key,
            )

            http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({"success": True, "data": response_body}, status=http_status)

        except InsufficientFundsError as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except InvalidRequestError as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Unexpected error creating payout: %s", exc)
            return Response(
                {"success": False, "error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PayoutDetailView(APIView):
    """GET /api/v1/payouts/<payout_id> — Single payout status."""

    def get(self, request, payout_id):
        try:
            payout = Payout.objects.select_related("bank_account").get(id=payout_id)
        except (Payout.DoesNotExist, ValueError):
            return Response(
                {"success": False, "error": "Payout not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PayoutSerializer(payout)
        return Response({"success": True, "data": serializer.data})
