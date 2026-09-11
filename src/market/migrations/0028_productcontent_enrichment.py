from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0027_product_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="productcontent",
            name="enrichment_reasons",
            field=models.JSONField(blank=True, default=list, verbose_name="Причины"),
        ),
        migrations.AddField(
            model_name="productcontent",
            name="enrichment_status",
            field=models.CharField(
                choices=[("ok", "Достаточно"), ("needs_enrichment", "Нужно обогащение")],
                db_index=True,
                default="needs_enrichment",
                max_length=32,
                verbose_name="Оценка описания",
            ),
        ),
    ]
