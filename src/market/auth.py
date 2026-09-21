from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import PartnerApiKey


class PartnerPrincipal:
    is_authenticated = True
    is_anonymous = False

    def __init__(self, key: PartnerApiKey):
        self.partner_key = key
        self.pk = key.pk
        self.id = key.pk

    def __str__(self):
        return self.partner_key.name


class PartnerApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = (request.headers.get("X-Api-Key") or "").strip()
        if not raw:
            auth = (request.headers.get("Authorization") or "").strip()
            prefix = "bearer "
            if auth.lower().startswith(prefix):
                raw = auth[len(prefix) :].strip()
        if not raw:
            return None
        key = PartnerApiKey.objects.filter(token=raw, is_active=True).first()
        if key is None:
            raise AuthenticationFailed("Неверный токен")
        return (PartnerPrincipal(key), key.token)

    def authenticate_header(self, request):
        return "Bearer"


class OptionalJWTAuthentication(JWTAuthentication):
    """JWT if the access token is valid; otherwise anonymous so guest checkout still works."""

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None

