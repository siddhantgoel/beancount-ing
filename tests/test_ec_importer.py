import datetime
from decimal import Decimal
from tempfile import gettempdir
from textwrap import dedent
from unittest import TestCase
import os
from datetime import date

from beancount.core.data import Balance, Transaction
from beancount_ing.ec import BANKS, ECImporter, PRE_HEADER


HEADER = ";".join(
    '"{}"'.format(field)
    for field in (
        "Buchung",
        "Valuta",
        "Auftraggeber/Empfänger",
        "Buchungstext",
        "Verwendungszweck",
        "Saldo",
        "Währung",
        "Betrag",
        "Währung",
    )
)


def path_for_temp_file(name):
    return os.path.join(gettempdir(), name)


class ECImporterTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.iban = "DE99999999999999999999"
        self.formatted_iban = "DE99 9999 9999 9999 9999 99"
        self.user = "Max Mustermann"
        self.filename = path_for_temp_file("{}.csv".format(self.iban))

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

        super().tearDown()

    def _format_data(self, string, **kwargs):
        kwargs.update(
            {
                "formatted_iban": self.formatted_iban,
                "header": HEADER,
                "user": self.user,
                "pre_header": PRE_HEADER,
            }
        )
        return dedent(string).format(**kwargs).lstrip().encode("ISO-8859-1")

    def test_identify_correct(self):
        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        for bank in BANKS:
            with open(self.filename, "wb") as fd:
                fd.write(
                    self._format_data(
                        """
                        Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                        ;Letztes Update: aktuell

                        IBAN;{formatted_iban}
                        Kontoname;Extra-Konto
                        Bank;{bank}
                        Kunde;{user}
                        Zeitraum;01.06.2018 - 30.06.2018
                        Saldo;5.000,00;EUR

                        {pre_header}

                        {header}
                        08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;REWE SAGT DANKE;1.234,00;EUR;500,00;EUR
                        """,  # NOQA
                        bank=bank,
                    )
                )

            self.assertTrue(importer.identify(self.filename))

    def test_identify_invalid_iban(self):
        other_iban = "DE00000000000000000000"

        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    {pre_header}

                    {header}
                    """  # NOQA
                )
            )

        importer = ECImporter(other_iban, "Assets:ING:Extra", self.user)

        self.assertFalse(importer.identify(self.filename))

    def test_identify_invalid_user(self):
        other_user = "Ken Adams"

        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    {pre_header}

                    {header}
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", other_user)

        self.assertFalse(importer.identify(self.filename))

    def test_identify_invalid_bank(self):
        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;Nope
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    {pre_header}

                    {header}
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;REWE SAGT DANKE;1.234,00;EUR;500,00;EUR
                    """  # NOQA
                )
            )

        self.assertFalse(importer.identify(self.filename))

    def test_extract_no_transactions(self):
        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    {pre_header}

                    {header}
                    """  # NOQA
                )
            )

        directives = importer.extract(self.filename)

        self.assertFalse(directives)

    def test_extract_transactions(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    {pre_header}

                    {header}
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        self.assertEqual(len(directives), 1)

        self.assertEqual(directives[0].date, datetime.date(2018, 6, 8))
        self.assertEqual(directives[0].payee, "REWE Filialen Voll")
        self.assertEqual(directives[0].narration, "Gutschrift REWE SAGT DANKE")

        self.assertEqual(len(directives[0].postings), 1)
        self.assertEqual(directives[0].postings[0].account, "Assets:ING:Extra")
        self.assertEqual(directives[0].postings[0].units.currency, "EUR")
        self.assertEqual(directives[0].postings[0].units.number, Decimal("-500.00"))

    def test_optional_sorting_line(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    {header}
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 2 balance assertions
        self.assertEqual(len(directives), 1 + 2)

    def test_category_included(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                    ;Letztes Update: aktuell

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 2 balance assertions
        self.assertEqual(len(directives), 1 + 2)

    def test_no_second_header(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 2 balance assertions
        self.assertEqual(len(directives), 1 + 2)

    def test_duplicate_waehrung_field_handled_correctly(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;USD;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 1 balance assertion
        # (opening balance cannot be calculated due to currency mismatch)
        self.assertEqual(len(directives), 1 + 1)
        self.assertEqual(directives[0].postings[0].units.currency, "EUR")

    def test_bad_sorting_no_balances(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Betrag absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;USD;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + no balance assertion (not sorted by date)
        self.assertEqual(len(directives), 1)
        self.assertFalse(isinstance(directives[0], Balance))

    def test_ascending_by_date_single(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum aufsteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 2 balance assertions
        self.assertEqual(len(directives), 1 + 2)

        self.assertTrue(isinstance(directives[0], Transaction))

        # Test opening balance
        self.assertTrue(isinstance(directives[1], Balance))
        self.assertEqual(directives[1].date, date(2018, 6, 1))
        self.assertEqual(directives[1].amount.number, 1734.0)
        self.assertEqual(directives[1].amount.currency, "EUR")

        # Test closing balance
        self.assertTrue(isinstance(directives[2], Balance))
        self.assertEqual(directives[2].date, date(2018, 7, 1))
        self.assertEqual(directives[2].amount.number, 1234.0)
        self.assertEqual(directives[2].amount.currency, "EUR")

    def test_ascending_by_date_multiple(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum aufsteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    08.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.200,00;EUR;-34,00;EUR
                    15.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.100,00;EUR;-100,00;EUR
                    15.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.000,00;EUR;-100,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 4 directives + 2 balance assertions
        self.assertEqual(len(directives), 4 + 2)
        # Test opening balance
        self.assertEqual(directives[4].date, date(2018, 6, 1))
        self.assertEqual(directives[4].amount.number, 1734.0)
        self.assertEqual(directives[4].amount.currency, "EUR")
        # Test closing balance
        self.assertEqual(directives[5].date, date(2018, 7, 1))
        self.assertEqual(directives[5].amount.number, 1000.0)
        self.assertEqual(directives[5].amount.currency, "EUR")

    def test_descending_by_date_single(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 1 transaction + 2 balance assertions
        self.assertEqual(len(directives), 1 + 2)
        # Test opening balance
        self.assertEqual(directives[1].date, date(2018, 6, 1))
        self.assertEqual(directives[1].amount.number, 1734.0)
        self.assertEqual(directives[1].amount.currency, "EUR")
        # Test closing balance
        self.assertEqual(directives[2].date, date(2018, 7, 1))
        self.assertEqual(directives[2].amount.number, 1234.0)
        self.assertEqual(directives[2].amount.currency, "EUR")

    def test_descending_by_date_multiple(self):
        with open(self.filename, "wb") as fd:
            fd.write(
                self._format_data(
                    """
                    Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00

                    IBAN;{formatted_iban}
                    Kontoname;Extra-Konto
                    Bank;ING
                    Kunde;{user}
                    Zeitraum;01.06.2018 - 30.06.2018
                    Saldo;5.000,00;EUR

                    Sortierung;Datum absteigend

                    {pre_header}

                    "Buchung";"Valuta";"Auftraggeber/Empfänger";"Buchungstext";"Kategorie";"Verwendungszweck";"Saldo";"Währung";"Betrag";"Währung"
                    15.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.000,00;EUR;-100,00;EUR
                    15.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.100,00;EUR;-100,00;EUR
                    08.06.2018;08.06.2018;LIDL;Lastschrift;Kategorie;LIDL SAGT DANKE;1.200,00;EUR;-34,00;EUR
                    08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;Kategorie;REWE SAGT DANKE;1.234,00;EUR;-500,00;EUR
                    """  # NOQA
                )
            )

        importer = ECImporter(self.iban, "Assets:ING:Extra", self.user)

        directives = importer.extract(self.filename)

        # 4 directives + 2 balance assertions
        self.assertEqual(len(directives), 4 + 2)
        # Test opening balance
        self.assertEqual(directives[4].date, date(2018, 6, 1))
        self.assertEqual(directives[4].amount.number, 1734.0)
        self.assertEqual(directives[4].amount.currency, "EUR")
        # Test closing balance
        self.assertEqual(directives[5].date, date(2018, 7, 1))
        self.assertEqual(directives[5].amount.number, 1000.0)
        self.assertEqual(directives[5].amount.currency, "EUR")
