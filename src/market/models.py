import uuid

from django.db import models


class GroupOfGoods(models.Model):
    default_order = models.CharField(max_length=128)
    site_order = models.IntegerField(blank=True, null=True, verbose_name='Порядок на сайте')
    deleted = models.BooleanField(verbose_name='Крупный опт')
    isaction = models.BooleanField(default=True, verbose_name='Показывать на сайте')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    name = models.CharField(verbose_name="Наименование группы", max_length=128)
    parent_id = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', blank=True, null=True)
    updated = models.DateTimeField(verbose_name='Обновлено')


class GoodsModel(models.Model):
    title = models.CharField(max_length=256, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    category = models.ForeignKey(GroupOfGoods, on_delete=models.CASCADE, related_name='group', verbose_name='Категория')
    type = models.CharField(max_length=128, verbose_name='Тип')
    stock = models.PositiveIntegerField(blank=True, null=True, verbose_name='Остатки')
    bestseller = models.BooleanField(blank=True, null=True, verbose_name='Бест-селлер')
    official_price = models.PositiveIntegerField(blank=True, null=True, verbose_name='Официальная цена')
    retail_price = models.PositiveIntegerField(blank=True, null=True, verbose_name='Розничная цена')
    wholesale_price = models.PositiveIntegerField(blank=True, null=True, verbose_name='Оптовая цена')
    large_wholesale_price = models.PositiveIntegerField(blank=True, null=True, verbose_name='Крупный опт')


class SiteOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплату"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"
        CANCELLED = "cancelled", "Отменён"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    first_name = models.CharField(max_length=128, verbose_name="ФИО")
    phone = models.CharField(max_length=64, verbose_name="Телефон")
    phone_digits = models.CharField(max_length=32, blank=True, verbose_name="Телефон (цифры)")
    email = models.EmailField(verbose_name="Email")
    country = models.CharField(max_length=64, verbose_name="Страна")
    city = models.CharField(max_length=128, verbose_name="Город")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    postal_code = models.CharField(max_length=32, blank=True, verbose_name="Индекс")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    amount_krw = models.PositiveIntegerField(verbose_name="Сумма, ₩")
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма, USD")
    usd_rate_snapshot = models.DecimalField(
        max_digits=16, decimal_places=8, blank=True, null=True, verbose_name="Курс KRW→USD"
    )
    paypal_order_id = models.CharField(max_length=64, blank=True, db_index=True)
    paypal_capture_id = models.CharField(max_length=64, blank=True)
    paypal_receipt_url = models.TextField(blank=True, verbose_name="Ссылка на чек PayPal")
    paypal_payload = models.TextField(blank=True)
    business_ru_partner_id = models.CharField(max_length=32, blank=True)
    business_ru_order_id = models.CharField(max_length=32, blank=True)
    business_ru_payment_id = models.CharField(max_length=32, blank=True, verbose_name="ID оплаты Business.Ru")
    business_ru_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Заказ с сайта"
        verbose_name_plural = "Заказы с сайта"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.public_id} ({self.get_status_display()})"


class SiteOrderItem(models.Model):
    order = models.ForeignKey(SiteOrder, on_delete=models.CASCADE, related_name="items")
    good = models.ForeignKey(
        GoodsModel, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Товар"
    )
    good_id_snapshot = models.PositiveIntegerField(verbose_name="ID товара")
    title = models.CharField(max_length=256, verbose_name="Название")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price_krw = models.PositiveIntegerField(verbose_name="Цена, ₩")
    line_total_krw = models.PositiveIntegerField(verbose_name="Сумма, ₩")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.title} × {self.quantity}"


class ImageModel(models.Model):
    group = models.ForeignKey(GroupOfGoods, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Группа')
    good = models.ForeignKey(GoodsModel, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Товар')
    name = models.CharField(verbose_name="Название", max_length=128)
    sort = models.IntegerField(null=True, blank=True, verbose_name='Sort')
    url = models.TextField(verbose_name='URL')
