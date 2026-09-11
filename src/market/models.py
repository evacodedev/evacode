from datetime import time as dt_time
import secrets

from django.db import models


PUBLIC_ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_public_id() -> str:
    return "".join(secrets.choice(PUBLIC_ID_ALPHABET) for _ in range(8))


def generate_partner_token() -> str:
    return secrets.token_urlsafe(32)


CONTENT_LANGUAGES = (
    ("ru", "Русский"),
    ("en", "English"),
    ("ko", "한국어"),
)

CONTENT_BLOCK_KINDS = (
    ("lead", "Лид"),
    ("about", "О товаре"),
    ("benefits", "Преимущества"),
    ("ingredients", "Компоненты"),
    ("texture", "Текстура"),
    ("how_to_use", "Применение"),
    ("suitable_for", "Подходит для"),
    ("volume", "Объём"),
    ("weight", "Вес"),
    ("set_contents", "Состав набора"),
    ("rest", "Остаток"),
)


class ProductBrand(models.Model):
    slug = models.SlugField(max_length=160, unique=True, allow_unicode=True, verbose_name="Код")

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ("slug",)

    def __str__(self):
        ru = self.translations.filter(language="ru").first()
        return (ru.name if ru else "") or self.slug


class ProductBrandI18n(models.Model):
    brand = models.ForeignKey(ProductBrand, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=8, choices=CONTENT_LANGUAGES, verbose_name="Язык")
    name = models.CharField(max_length=256, verbose_name="Название")

    class Meta:
        verbose_name = "Перевод бренда"
        verbose_name_plural = "Переводы брендов"
        constraints = [
            models.UniqueConstraint(fields=("brand", "language"), name="market_brand_i18n_uniq"),
        ]

    def __str__(self):
        return f"{self.language}: {self.name}"


class ProductKind(models.Model):
    slug = models.SlugField(max_length=160, unique=True, verbose_name="Код")

    class Meta:
        verbose_name = "Тип товара"
        verbose_name_plural = "Типы товаров"
        ordering = ("slug",)

    def __str__(self):
        ru = self.translations.filter(language="ru").first()
        return (ru.name if ru else "") or self.slug


class ProductKindI18n(models.Model):
    kind = models.ForeignKey(ProductKind, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=8, choices=CONTENT_LANGUAGES, verbose_name="Язык")
    name = models.CharField(max_length=256, verbose_name="Название")

    class Meta:
        verbose_name = "Перевод типа товара"
        verbose_name_plural = "Переводы типов товаров"
        constraints = [
            models.UniqueConstraint(fields=("kind", "language"), name="market_kind_i18n_uniq"),
        ]

    def __str__(self):
        return f"{self.language}: {self.name}"


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
    weight = models.PositiveIntegerField(blank=True, null=True, verbose_name='Вес, г')
    queue = models.IntegerField(blank=True, null=True, verbose_name='Очередь в списке')
    content_brand = models.ForeignKey(
        ProductBrand,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="goods",
        verbose_name="Бренд (контент)",
    )
    content_kind = models.ForeignKey(
        ProductKind,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="goods",
        verbose_name="Тип (контент)",
    )

    def __str__(self):
        return self.title or str(self.id)


class EmsRateColumn(models.Model):
    code = models.CharField(max_length=64, unique=True, verbose_name="Код колонки")
    title = models.CharField(max_length=128, verbose_name="Название")
    sort = models.IntegerField(default=0, verbose_name="Порядок")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Колонка тарифа EMS"
        verbose_name_plural = "Колонки тарифа EMS"
        ordering = ("sort", "code")

    def __str__(self):
        return self.title or self.code


class EmsRate(models.Model):
    column = models.ForeignKey(
        EmsRateColumn,
        on_delete=models.CASCADE,
        related_name="rates",
        verbose_name="Колонка",
    )
    weight_grams = models.PositiveIntegerField(verbose_name="Вес до, г")
    price_krw = models.PositiveIntegerField(verbose_name="Цена, ₩")

    class Meta:
        verbose_name = "Ставка EMS"
        verbose_name_plural = "Ставки EMS"
        ordering = ("column", "weight_grams")
        constraints = [
            models.UniqueConstraint(
                fields=("column", "weight_grams"),
                name="market_emsrate_column_weight_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.column_id} {self.weight_grams}g = {self.price_krw}₩"


class EmsDestination(models.Model):
    code = models.CharField(max_length=16, unique=True, verbose_name="Код")
    name = models.CharField(max_length=128, verbose_name="Название")
    rate_column = models.ForeignKey(
        EmsRateColumn,
        on_delete=models.SET_NULL,
        related_name="destinations",
        blank=True,
        null=True,
        verbose_name="Колонка тарифа",
    )
    sort = models.IntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать")

    class Meta:
        verbose_name = "Направление EMS"
        verbose_name_plural = "Направления EMS"
        ordering = ("sort", "code")

    def __str__(self):
        return self.name

    @property
    def can_calculate(self):
        return self.rate_column_id is not None


class SiteOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплату"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"
        CANCELLED = "cancelled", "Отменён"

    public_id = models.CharField(max_length=36, unique=True, editable=False, default=generate_public_id)
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
    shipping_method = models.CharField(max_length=16, blank=True, verbose_name="Способ доставки")
    shipping_destination = models.CharField(max_length=16, blank=True, verbose_name="Направление EMS")
    shipping_krw = models.PositiveIntegerField(default=0, verbose_name="Доставка, ₩")
    goods_krw = models.PositiveIntegerField(default=0, verbose_name="Товары, ₩")
    weight_grams = models.PositiveIntegerField(blank=True, null=True, verbose_name="Вес заказа, г")
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
    business_ru_order_number = models.CharField(max_length=32, blank=True, verbose_name="№ заказа покупателя")
    business_ru_payment_id = models.CharField(max_length=32, blank=True, verbose_name="ID оплаты Business.Ru")
    business_ru_payment_number = models.CharField(max_length=32, blank=True, verbose_name="№ входящей оплаты")
    business_ru_reservation_id = models.CharField(max_length=32, blank=True, verbose_name="ID резерва Business.Ru")
    business_ru_reservation_number = models.CharField(max_length=32, blank=True, verbose_name="№ резерва")
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


class PartnerApiKey(models.Model):
    name = models.CharField(max_length=128, verbose_name="Партнёр")
    token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        verbose_name="Токен",
        help_text="Если оставить пустым, сгенерируется при сохранении",
    )
    is_active = models.BooleanField(default=True, verbose_name="Включён")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        verbose_name = "Токен API партнёра"
        verbose_name_plural = "Токены API партнёров"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not (self.token or "").strip():
            self.token = generate_partner_token()
        else:
            self.token = self.token.strip()
        super().save(*args, **kwargs)


class CheckoutSettings(models.Model):
    paypal_enabled = models.BooleanField(
        default=False,
        verbose_name="PayPal на сайте",
        help_text="Ключи PayPal остаются в .env. Этот флаг только показывает оплату на витрине.",
    )
    telegram_enabled = models.BooleanField(
        default=False,
        verbose_name="Заказ в Telegram",
        help_text="Консультация в подвале сайта работает независимо от этого флага.",
    )

    class Meta:
        verbose_name = "Оплата на сайте"
        verbose_name_plural = "Оплата на сайте"

    def __str__(self):
        return "Оплата на сайте"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"paypal_enabled": False, "telegram_enabled": False},
        )
        return obj


class ApiKzSync(models.Model):
    WAREHOUSE_KZ = "KZ"
    WAREHOUSE_RU = "RU"
    WAREHOUSE_UZ = "UZ"
    WAREHOUSE_CHOICES = (
        (WAREHOUSE_KZ, "Казахстан"),
        (WAREHOUSE_RU, "Россия"),
        (WAREHOUSE_UZ, "Узбекистан"),
    )

    warehouse_code = models.CharField(
        max_length=8,
        choices=WAREHOUSE_CHOICES,
        default=WAREHOUSE_KZ,
        db_index=True,
        verbose_name="Склад",
    )
    store_id = models.CharField(max_length=32, blank=True, db_index=True, verbose_name="ID склада BR")
    run_at = models.DateTimeField(auto_now_add=True, verbose_name="Запуск")
    ok = models.BooleanField(default=False, verbose_name="Успешно")
    message = models.TextField(blank=True, verbose_name="Результат")
    inventory_id = models.CharField(max_length=32, blank=True, verbose_name="ID инвентаризации BR")
    inventory_number = models.CharField(max_length=32, blank=True, verbose_name="№ инвентаризации")
    posting_id = models.CharField(max_length=32, blank=True, verbose_name="ID оприходования BR")
    posting_number = models.CharField(max_length=32, blank=True, verbose_name="№ оприходования")
    charge_id = models.CharField(max_length=32, blank=True, verbose_name="ID списания BR")
    charge_number = models.CharField(max_length=32, blank=True, verbose_name="№ списания")
    prices_updated = models.PositiveIntegerField(default=0, verbose_name="Цен обновлено")
    prices_unchanged = models.PositiveIntegerField(default=0, verbose_name="Цен без изменений")
    prices_failed = models.PositiveIntegerField(default=0, verbose_name="Цен с ошибкой")
    prices_goods = models.PositiveIntegerField(default=0, verbose_name="Товаров с ценами")
    prices_list_id = models.CharField(max_length=32, blank=True, verbose_name="ID назначения цен BR")
    prices_list_number = models.CharField(max_length=32, blank=True, verbose_name="№ назначения цен")

    class Meta:
        verbose_name = "Запуск синхронизации"
        verbose_name_plural = "История синхронизаций"
        ordering = ("-run_at", "-id")

    def __str__(self):
        when = self.run_at.strftime("%Y-%m-%d %H:%M") if self.run_at else "—"
        return f"{self.get_warehouse_code_display()} {when}"


class ApiKzSyncSettings(models.Model):
    WEEKDAY_CHOICES = (
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    )

    enabled = models.BooleanField(
        default=False,
        verbose_name="Расписание включено",
        help_text="Пока выключено, фоновый воркер не запускает синхронизацию. Ручной запуск из истории работает всегда.",
    )
    weekdays = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Дни недели",
        help_text="Можно выбрать несколько дней. Время одно на все выбранные дни.",
    )
    run_time = models.TimeField(
        default=dt_time(3, 0),
        verbose_name="Время запуска",
        help_text="Часы и минуты в поясе сервера — смотрите часы на этой странице.",
    )

    class Meta:
        verbose_name = "Расписание синхронизации"
        verbose_name_plural = "Расписание синхронизации"

    def __str__(self):
        return "Расписание синхронизации KZ"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"enabled": False, "weekdays": "", "run_time": dt_time(3, 0)},
        )
        return obj


class ProductContent(models.Model):
    good = models.OneToOneField(
        GoodsModel,
        on_delete=models.CASCADE,
        related_name="pdp_content",
        verbose_name="Товар",
    )
    parsed_at = models.DateTimeField(auto_now=True, verbose_name="Разобрано")
    enrichment_status = models.CharField(
        max_length=32,
        choices=(
            ("ok", "Достаточно"),
            ("needs_enrichment", "Нужно обогащение"),
        ),
        default="needs_enrichment",
        db_index=True,
        verbose_name="Оценка описания",
    )
    enrichment_reasons = models.JSONField(default=list, blank=True, verbose_name="Причины")

    class Meta:
        verbose_name = "Контент карточки"
        verbose_name_plural = "Контент карточек"

    def __str__(self):
        return f"Контент {self.good_id}"


class ProductContentBlock(models.Model):
    content = models.ForeignKey(
        ProductContent,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Контент",
    )
    kind = models.CharField(max_length=32, choices=CONTENT_BLOCK_KINDS, verbose_name="Секция")
    sort = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Секция карточки"
        verbose_name_plural = "Секции карточек"
        ordering = ("sort", "id")
        constraints = [
            models.UniqueConstraint(fields=("content", "kind"), name="market_pdp_block_kind_uniq"),
        ]

    def __str__(self):
        return f"{self.content_id}:{self.kind}"


class ProductContentBlockI18n(models.Model):
    block = models.ForeignKey(
        ProductContentBlock,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name="Секция",
    )
    language = models.CharField(max_length=8, choices=CONTENT_LANGUAGES, verbose_name="Язык")
    heading = models.CharField(max_length=256, blank=True, verbose_name="Заголовок")
    body = models.TextField(blank=True, verbose_name="Текст")
    items = models.JSONField(default=list, blank=True, verbose_name="Пункты")

    class Meta:
        verbose_name = "Перевод секции"
        verbose_name_plural = "Переводы секций"
        constraints = [
            models.UniqueConstraint(fields=("block", "language"), name="market_pdp_block_i18n_uniq"),
        ]

    def __str__(self):
        return f"{self.block_id}:{self.language}"


class ImageModel(models.Model):
    group = models.ForeignKey(GroupOfGoods, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Группа')
    good = models.ForeignKey(GoodsModel, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Товар')
    name = models.CharField(verbose_name="Название", max_length=128)
    sort = models.IntegerField(null=True, blank=True, verbose_name='Sort')
    url = models.TextField(verbose_name='URL')
