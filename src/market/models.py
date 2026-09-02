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


class ImageModel(models.Model):
    group = models.ForeignKey(GroupOfGoods, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Группа')
    good = models.ForeignKey(GoodsModel, on_delete=models.CASCADE, related_name='images', blank=True, null=True, verbose_name='Товар')
    name = models.CharField(verbose_name="Название", max_length=128)
    sort = models.IntegerField(null=True, blank=True, verbose_name='Sort')
    url = models.TextField(verbose_name='URL')
