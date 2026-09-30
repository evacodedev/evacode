from django.test import SimpleTestCase

from market.business_ru_orders import _NOTE_LIMIT, _document_note
from market.models import SiteOrder


def _order(**extra):
    fields = {
        "public_id": "AB12CD34",
        "first_name": "Viktoria Fröhlich",
        "email": "viktoria_eberz@yahoo.de",
        "phone": "+4915170381990",
        "country": "Germany",
        "city": "Ebelsbach",
        "address": "Bayern, Steinbacher Weg 4, Apt. 4",
        "postal_code": "97500",
        "shipping_method": "ems",
    }
    fields.update(extra)
    return SiteOrder(**fields)


class DocumentNoteTests(SimpleTestCase):
    def test_note_lists_contacts_without_labels(self):
        self.assertEqual(
            _document_note(_order()),
            "Сайт AB12CD34 · Viktoria Fröhlich · viktoria_eberz@yahoo.de · +4915170381990"
            " · 97500, Germany, Ebelsbach, Bayern, Steinbacher Weg 4, Apt. 4",
        )

    def test_buyer_comment_is_not_in_note(self):
        note = _document_note(_order(comment="Позвонить после 18:00"))
        self.assertNotIn("Позвонить", note)
        self.assertLessEqual(len(note), _NOTE_LIMIT)

    def test_pickup_note(self):
        note = _document_note(_order(shipping_method="pickup"))
        self.assertTrue(note.endswith("· +4915170381990 · Самовывоз"))
