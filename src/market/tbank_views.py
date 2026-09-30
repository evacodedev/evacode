import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .tbank import iter_operations, save_operation, webhook_authorized

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TBankOperationWebhookView(APIView):
    """Вебхук Т-Банка «Операция по счету» (oper-feed-operation)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        allowed, status = webhook_authorized(request)
        if not allowed:
            return Response({"ok": False}, status=status)
        payloads = iter_operations(request.data)
        saved = 0
        for payload in payloads:
            row = save_operation(payload, source="webhook")
            if row is not None:
                saved += 1
                logger.info(
                    "T-Bank webhook %s %s %s",
                    row.operation_id,
                    row.match_status,
                    row.order.public_id if row.order_id else "-",
                )
        return Response({"ok": True, "saved": saved})
