from django.core.management.base import BaseCommand

from market.business_ru_orders import BusinessRuOrderClient


class Command(BaseCommand):
    help = "Печатает склады, статусы заказов, организации и сотрудников Business.Ru"

    def handle(self, *args, **options):
        client = BusinessRuOrderClient()
        sections = (
            ("stores", "Склады"),
            ("customerorderstatus", "Статусы заказов покупателей"),
            ("organizations", "Организации"),
            ("employees", "Сотрудники"),
            ("currentaccounts", "Расчётные счета"),
            ("paymentinoperations", "Виды операций входящих платежей"),
        )
        for model, title in sections:
            self.stdout.write(self.style.NOTICE(title))
            payload = client.request("get", model)
            for item in payload.get("result") or []:
                name = item.get("name") or item.get("full_name") or item.get("first_name") or item.get("number") or ""
                extra = ""
                if model == "currentaccounts":
                    extra = f"  organization_id={item.get('organization_id')}"
                self.stdout.write(f"  id={item.get('id')}  {name}{extra}")
            self.stdout.write("")
