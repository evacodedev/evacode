from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0026_apikzsyncsettings_weekdays"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductBrand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(allow_unicode=True, max_length=160, unique=True, verbose_name="Код")),
            ],
            options={
                "verbose_name": "Бренд",
                "verbose_name_plural": "Бренды",
                "ordering": ("slug",),
            },
        ),
        migrations.CreateModel(
            name="ProductKind",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=160, unique=True, verbose_name="Код")),
            ],
            options={
                "verbose_name": "Тип товара",
                "verbose_name_plural": "Типы товаров",
                "ordering": ("slug",),
            },
        ),
        migrations.CreateModel(
            name="ProductBrandI18n",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "language",
                    models.CharField(
                        choices=[("ru", "Русский"), ("en", "English"), ("ko", "한국어")],
                        max_length=8,
                        verbose_name="Язык",
                    ),
                ),
                ("name", models.CharField(max_length=256, verbose_name="Название")),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="market.productbrand",
                    ),
                ),
            ],
            options={
                "verbose_name": "Перевод бренда",
                "verbose_name_plural": "Переводы брендов",
            },
        ),
        migrations.CreateModel(
            name="ProductKindI18n",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "language",
                    models.CharField(
                        choices=[("ru", "Русский"), ("en", "English"), ("ko", "한국어")],
                        max_length=8,
                        verbose_name="Язык",
                    ),
                ),
                ("name", models.CharField(max_length=256, verbose_name="Название")),
                (
                    "kind",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="market.productkind",
                    ),
                ),
            ],
            options={
                "verbose_name": "Перевод типа товара",
                "verbose_name_plural": "Переводы типов товаров",
            },
        ),
        migrations.AddField(
            model_name="goodsmodel",
            name="content_brand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="goods",
                to="market.productbrand",
                verbose_name="Бренд (контент)",
            ),
        ),
        migrations.AddField(
            model_name="goodsmodel",
            name="content_kind",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="goods",
                to="market.productkind",
                verbose_name="Тип (контент)",
            ),
        ),
        migrations.CreateModel(
            name="ProductContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("parsed_at", models.DateTimeField(auto_now=True, verbose_name="Разобрано")),
                (
                    "good",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pdp_content",
                        to="market.goodsmodel",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Контент карточки",
                "verbose_name_plural": "Контент карточек",
            },
        ),
        migrations.CreateModel(
            name="ProductContentBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("lead", "Лид"),
                            ("about", "О товаре"),
                            ("benefits", "Преимущества"),
                            ("ingredients", "Компоненты"),
                            ("texture", "Текстура"),
                            ("how_to_use", "Применение"),
                            ("suitable_for", "Подходит для"),
                            ("volume", "Объём"),
                            ("weight", "Вес"),
                            ("rest", "Остаток"),
                        ],
                        max_length=32,
                        verbose_name="Секция",
                    ),
                ),
                ("sort", models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")),
                (
                    "content",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocks",
                        to="market.productcontent",
                        verbose_name="Контент",
                    ),
                ),
            ],
            options={
                "verbose_name": "Секция карточки",
                "verbose_name_plural": "Секции карточек",
                "ordering": ("sort", "id"),
            },
        ),
        migrations.CreateModel(
            name="ProductContentBlockI18n",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "language",
                    models.CharField(
                        choices=[("ru", "Русский"), ("en", "English"), ("ko", "한국어")],
                        max_length=8,
                        verbose_name="Язык",
                    ),
                ),
                ("heading", models.CharField(blank=True, max_length=256, verbose_name="Заголовок")),
                ("body", models.TextField(blank=True, verbose_name="Текст")),
                ("items", models.JSONField(blank=True, default=list, verbose_name="Пункты")),
                (
                    "block",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="market.productcontentblock",
                        verbose_name="Секция",
                    ),
                ),
            ],
            options={
                "verbose_name": "Перевод секции",
                "verbose_name_plural": "Переводы секций",
            },
        ),
        migrations.AddConstraint(
            model_name="productbrandi18n",
            constraint=models.UniqueConstraint(fields=("brand", "language"), name="market_brand_i18n_uniq"),
        ),
        migrations.AddConstraint(
            model_name="productkindi18n",
            constraint=models.UniqueConstraint(fields=("kind", "language"), name="market_kind_i18n_uniq"),
        ),
        migrations.AddConstraint(
            model_name="productcontentblock",
            constraint=models.UniqueConstraint(fields=("content", "kind"), name="market_pdp_block_kind_uniq"),
        ),
        migrations.AddConstraint(
            model_name="productcontentblocki18n",
            constraint=models.UniqueConstraint(fields=("block", "language"), name="market_pdp_block_i18n_uniq"),
        ),
    ]
