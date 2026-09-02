from django.core.management.base import BaseCommand, CommandError

from market.business_ru_orders import export_paid_order
from market.models import SiteOrder


class Command(BaseCommand):
    help = "Повторно выгрузить оплаченный заказ сайта в Business.Ru"

    def add_arguments(self, parser):
        parser.add_argument("public_id", help="UUID заказа с сайта")

    def handle(self, *args, **options):
        order = SiteOrder.objects.filter(public_id=options["public_id"]).first()
        if not order:
            raise CommandError("Заказ не найден")
        if order.status != SiteOrder.Status.PAID:
            raise CommandError(f"Заказ не оплачен: {order.status}")
        export_paid_order(order)
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f"Business.Ru заказ {order.business_ru_order_id}, партнёр {order.business_ru_partner_id}"
        ))
