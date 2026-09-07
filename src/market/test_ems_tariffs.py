from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from market.ems_tariffs import ems_price_krw, import_ems_xlsx, parse_ems_xlsx
from market.models import EmsDestination, EmsRate, EmsRateColumn


def make_ems_xlsx() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "2017. 7. 1일부터 적용"
    sheet["A2"] = "중량 단계(kg)"
    sheet["B3"] = "호주"
    sheet["C3"] = "독일"
    sheet["A4"] = "0.3 까지"
    sheet["B4"] = 20.5
    sheet["C4"] = 28
    sheet["A10"] = "비서류"
    sheet["A11"] = "2026. 7. 1일부터 적용"
    sheet["A12"] = "중량 단계"
    sheet["B12"] = "국제특급우편 비서류 요금(원)"
    sheet["A13"] = "(kg)"
    sheet["B13"] = "호주"
    sheet["C13"] = "독일"
    sheet["A14"] = "0.5까지"
    sheet["B14"] = 33.5
    sheet["C14"] = 43.5
    sheet["A15"] = "1〃"
    sheet["B15"] = 40.5
    sheet["C15"] = 50
    sheet["A16"] = "2〃"
    sheet["B16"] = 55
    sheet["C16"] = 60.5
    sheet["A20"] = "중량 단계"
    sheet["B20"] = "국제특급우편 비서류 요금(원)"
    sheet["A21"] = "(kg)"
    sheet["B21"] = "러시아"
    sheet["C21"] = "3지역"
    sheet["A22"] = "0.5까지"
    sheet["B22"] = 30.5
    sheet["C22"] = 37.5
    sheet["A23"] = "1〃"
    sheet["B23"] = 39.5
    sheet["C23"] = 43.5
    sheet["A24"] = "2〃"
    sheet["B24"] = 57
    sheet["C24"] = 54.5
    sheet["A30"] = "(kg)"
    sheet["B30"] = "프랑스"
    sheet["C30"] = "스페인"
    sheet["D30"] = "영국"
    sheet["E30"] = "미국"
    sheet["A31"] = "1〃"
    sheet["B31"] = 36
    sheet["C31"] = 33.5
    sheet["D31"] = 44.5
    sheet["E31"] = 46
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class EmsTariffImportTests(TestCase):
    def test_parse_skips_documents_and_multiplies_by_thousand(self):
        parsed = parse_ems_xlsx(BytesIO(make_ems_xlsx()))
        self.assertNotIn(300, parsed["columns"]["호주"])
        self.assertEqual(parsed["columns"]["호주"][500], 33500)
        self.assertEqual(parsed["columns"]["러시아"][1000], 39500)
        self.assertEqual(parsed["columns"]["독일"][1000], 50000)
        self.assertEqual(parsed["columns"]["3지역"][1000], 43500)

    def test_import_binds_empty_destinations_and_keeps_existing(self):
        custom, _ = EmsRateColumn.objects.get_or_create(code="custom", defaults={"title": "custom"})
        kz = EmsDestination.objects.get(code="KZ")
        kz.rate_column = custom
        kz.save(update_fields=["rate_column"])

        import_ems_xlsx(BytesIO(make_ems_xlsx()))

        self.assertEqual(EmsDestination.objects.get(code="KZ").rate_column_id, custom.id)
        self.assertEqual(EmsDestination.objects.get(code="RU").rate_column.code, "러시아")
        self.assertIsNone(EmsDestination.objects.get(code="KR").rate_column_id)
        self.assertEqual(ems_price_krw("RU", 900), 39500)
        self.assertEqual(ems_price_krw("KZ", 1000), None)
        self.assertEqual(ems_price_krw("EU", 1000), 43500)
        self.assertIsNone(ems_price_krw("KR", 1000))
        self.assertEqual(EmsRate.objects.filter(column__code="러시아").count(), 3)
        self.assertEqual(EmsRateColumn.objects.get(code="러시아").title, "Russia")
        self.assertEqual(EmsRateColumn.objects.get(code="3지역").title, "Zone 3")
        self.assertEqual(EmsRateColumn.objects.get(code="독일").title, "Germany")

    def test_admin_upload(self):
        User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.post(
            reverse("admin:market_emsdestination_import_xlsx"),
            {
                "xlsx": SimpleUploadedFile(
                    "ems_price.xlsx",
                    make_ems_xlsx(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ems_price_krw("US", 1000), 46000)
        self.assertEqual(ems_price_krw("GB", 1000), 44500)
