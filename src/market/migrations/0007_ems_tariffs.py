from django.db import migrations, models


def seed_ems_destinations(apps, schema_editor):
    EmsRateColumn = apps.get_model("market", "EmsRateColumn")
    EmsDestination = apps.get_model("market", "EmsDestination")
    destinations = (
        ("DE", "Германия", "독일", 10),
        ("FR", "Франция", "프랑스", 20),
        ("ES", "Испания", "스페인", 30),
        ("GB", "Великобритания", "영국", 40),
        ("US", "США", "미국", 50),
        ("RU", "Россия", "러시아", 60),
        ("EU", "Европа (остальные)", "3지역", 70),
        ("UA", "Украина", "3지역", 80),
        ("TR", "Турция", "3지역", 90),
        ("KZ", "Казахстан", "3지역", 100),
        ("UZ", "Узбекистан", "3지역", 110),
        ("KG", "Кыргызстан", "3지역", 120),
        ("KR", "Корея", None, 130),
    )
    columns = {}
    for sort, code in enumerate(sorted({item[2] for item in destinations if item[2]})):
        columns[code], _ = EmsRateColumn.objects.get_or_create(
            code=code,
            defaults={"title": code, "sort": sort},
        )
    for code, name, column_code, sort in destinations:
        defaults = {"name": name, "sort": sort, "is_active": True}
        if column_code:
            defaults["rate_column"] = columns[column_code]
        EmsDestination.objects.get_or_create(code=code, defaults=defaults)


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0006_goodsmodel_queue"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmsRateColumn",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True, verbose_name="Код колонки")),
                ("title", models.CharField(max_length=128, verbose_name="Название")),
                ("sort", models.IntegerField(default=0, verbose_name="Порядок")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
            ],
            options={
                "verbose_name": "Колонка тарифа EMS",
                "verbose_name_plural": "Колонки тарифа EMS",
                "ordering": ("sort", "code"),
            },
        ),
        migrations.CreateModel(
            name="EmsDestination",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=16, unique=True, verbose_name="Код")),
                ("name", models.CharField(max_length=128, verbose_name="Название")),
                ("sort", models.IntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Показывать")),
                (
                    "rate_column",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="destinations",
                        to="market.emsratecolumn",
                        verbose_name="Колонка тарифа",
                    ),
                ),
            ],
            options={
                "verbose_name": "Направление EMS",
                "verbose_name_plural": "Направления EMS",
                "ordering": ("sort", "code"),
            },
        ),
        migrations.CreateModel(
            name="EmsRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight_grams", models.PositiveIntegerField(verbose_name="Вес до, г")),
                ("price_krw", models.PositiveIntegerField(verbose_name="Цена, ₩")),
                (
                    "column",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="rates",
                        to="market.emsratecolumn",
                        verbose_name="Колонка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ставка EMS",
                "verbose_name_plural": "Ставки EMS",
                "ordering": ("column", "weight_grams"),
            },
        ),
        migrations.AddConstraint(
            model_name="emsrate",
            constraint=models.UniqueConstraint(
                fields=("column", "weight_grams"),
                name="market_emsrate_column_weight_uniq",
            ),
        ),
        migrations.RunPython(seed_ems_destinations, migrations.RunPython.noop),
    ]
