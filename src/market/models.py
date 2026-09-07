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
    weight = models.PositiveIntegerField(blank=True, null=True, verbose_name='Вес, г')
    queue = models.IntegerField(blank=True, null=True, verbose_name='Очередь в списке')


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


class ImageModel(models.Model):
    group = models.ForeignKey(GroupOfGoods, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Группа')
    good = models.ForeignKey(GoodsModel, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Товар')
    name = models.CharField(verbose_name="Название", max_length=128)
    sort = models.IntegerField(null=True, blank=True, verbose_name='Sort')
    url = models.TextField(verbose_name='URL')
