import logging

from django.conf import settings
from django.contrib.auth.models import User
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccountProfile

logger = logging.getLogger(__name__)


def google_client_id() -> str:
    return (getattr(settings, "GOOGLE_CLIENT_ID", "") or "").strip()


def user_from_google_idinfo(idinfo: dict) -> User:
    email = (idinfo.get("email") or "").strip().lower()
    if not email:
        raise ValueError("В токене Google нет email")
    if not idinfo.get("email_verified", True):
        raise ValueError("Email Google не подтверждён")

    first_name = (idinfo.get("given_name") or idinfo.get("name") or "").strip()[:150]
    last_name = (idinfo.get("family_name") or "").strip()[:150]

    user = User.objects.filter(username__iexact=email).first() or User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User(username=email[:150], email=email)
        user.set_unusable_password()
        user.first_name = first_name
        user.last_name = last_name
        user.save()
    else:
        changed = []
        if not (user.email or "").strip():
            user.email = email
            changed.append("email")
        if first_name and not (user.first_name or "").strip():
            user.first_name = first_name
            changed.append("first_name")
        if last_name and not (user.last_name or "").strip():
            user.last_name = last_name
            changed.append("last_name")
        if changed:
            user.save(update_fields=changed)

    AccountProfile.objects.get_or_create(user=user)
    return user


class GoogleConfigView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        client_id = google_client_id()
        return Response(
            {
                "enabled": bool(client_id),
                "client_id": client_id,
            }
        )


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        from .views import _auth_payload

        client_id = google_client_id()
        if not client_id:
            return Response({"detail": "Вход через Google сейчас недоступен"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        credential = (request.data.get("credential") or request.data.get("id_token") or "").strip()
        if not credential:
            return Response({"detail": "Нет токена Google"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                audience=client_id,
                clock_skew_in_seconds=10,
            )
        except ValueError:
            logger.exception("Google id_token verification failed")
            return Response({"detail": "Не удалось проверить вход Google"}, status=status.HTTP_400_BAD_REQUEST)

        issuer = idinfo.get("iss")
        if issuer not in ("accounts.google.com", "https://accounts.google.com"):
            return Response({"detail": "Неверный издатель токена Google"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = user_from_google_idinfo(idinfo)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(_auth_payload(user))
