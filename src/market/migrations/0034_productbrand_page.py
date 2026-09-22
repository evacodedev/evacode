from django.db import migrations, models


def seed_jogabi(apps, schema_editor):
    from django.db.models import Q

    from market.brand_pages import JOGABI_PAGE

    ProductBrand = apps.get_model("market", "ProductBrand")
    ProductBrandI18n = apps.get_model("market", "ProductBrandI18n")
    GoodsModel = apps.get_model("market", "GoodsModel")
    data = JOGABI_PAGE
    brand, _created = ProductBrand.objects.get_or_create(slug=data["slug"])
    brand.page_published = data["page_published"]
    brand.official_url = data["official_url"]
    brand.native_caption = data["native_caption"]
    brand.logo = data["logo"]
    brand.hero = data["hero"]
    brand.history_image = data["history_image"]
    brand.save()
    ProductBrandI18n.objects.update_or_create(
        brand=brand,
        language="ru",
        defaults={
            "name": data["name"],
            "lead": data["lead"],
            "history": data["history"],
            "mission": data["mission"],
            "facts": data["facts"],
            "lines": data["lines"],
        },
    )
    GoodsModel.objects.filter(
        Q(title__icontains="jogabi") | Q(title__icontains="jagobi") | Q(title__icontains="조가비")
    ).update(content_brand=brand)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0033_siteorder_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="productbrand",
            name="page_published",
            field=models.BooleanField(default=False, verbose_name="Страница на сайте"),
        ),
        migrations.AddField(
            model_name="productbrand",
            name="official_url",
            field=models.URLField(blank=True, verbose_name="Официальный сайт"),
        ),
        migrations.AddField(
            model_name="productbrand",
            name="native_caption",
            field=models.CharField(
                blank=True,
                help_text="Не перевод имени, например 이화조개비",
                max_length=128,
                verbose_name="Подпись на исконном языке",
            ),
        ),
        migrations.AddField(
            model_name="productbrand",
            name="logo",
            field=models.CharField(blank=True, max_length=512, verbose_name="Логотип"),
        ),
        migrations.AddField(
            model_name="productbrand",
            name="hero",
            field=models.CharField(blank=True, max_length=512, verbose_name="Hero"),
        ),
        migrations.AddField(
            model_name="productbrand",
            name="history_image",
            field=models.CharField(blank=True, max_length=512, verbose_name="Фото истории"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="lead",
            field=models.TextField(blank=True, verbose_name="Лид"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="history",
            field=models.TextField(blank=True, verbose_name="История"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="mission",
            field=models.TextField(blank=True, verbose_name="Миссия"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="facts",
            field=models.JSONField(blank=True, default=list, verbose_name="Факты"),
        ),
        migrations.AddField(
            model_name="productbrandi18n",
            name="lines",
            field=models.JSONField(blank=True, default=list, verbose_name="Линии"),
        ),
        migrations.RunPython(seed_jogabi, noop),
    ]
