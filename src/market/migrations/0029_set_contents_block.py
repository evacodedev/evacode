from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0028_productcontent_enrichment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productcontentblock",
            name="kind",
            field=models.CharField(
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
                    ("set_contents", "Состав набора"),
                    ("rest", "Остаток"),
                ],
                max_length=32,
                verbose_name="Секция",
            ),
        ),
    ]
