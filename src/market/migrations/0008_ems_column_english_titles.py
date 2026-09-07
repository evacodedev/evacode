from django.db import migrations

COLUMN_TITLES_EN = {
    "호주": "Australia",
    "브라질": "Brazil",
    "캐나다": "Canada",
    "중국": "China",
    "프랑스": "France",
    "독일": "Germany",
    "홍콩": "Hong Kong",
    "인도네시아": "Indonesia",
    "일본": "Japan",
    "말레이시아": "Malaysia",
    "뉴질랜드": "New Zealand",
    "필리핀": "Philippines",
    "러시아": "Russia",
    "싱가포르": "Singapore",
    "스페인": "Spain",
    "대만": "Taiwan",
    "태국": "Thailand",
    "영국": "United Kingdom",
    "미국": "United States",
    "베트남": "Vietnam",
    "1지역": "Zone 1",
    "2지역": "Zone 2",
    "3지역": "Zone 3",
    "4지역": "Zone 4",
}


def apply_english_titles(apps, schema_editor):
    EmsRateColumn = apps.get_model("market", "EmsRateColumn")
    for column in EmsRateColumn.objects.all():
        title = COLUMN_TITLES_EN.get(column.code)
        if title and column.title != title:
            column.title = title
            column.save(update_fields=["title"])


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0007_ems_tariffs"),
    ]

    operations = [
        migrations.RunPython(apply_english_titles, migrations.RunPython.noop),
    ]
