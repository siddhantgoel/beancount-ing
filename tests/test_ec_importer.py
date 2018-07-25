from tempfile import gettempdir
from textwrap import dedent
from unittest import TestCase
import os

from beancount_ing_diba.ec import ECImporter, FIELDS


HEADER = ';'.join('"{}"'.format(field) for field in FIELDS)


def path_for_temp_file(name):
    return os.path.join(gettempdir(), name)


class ECImporterTestCase(TestCase):
    def setUp(self):
        super(ECImporterTestCase, self).setUp()

        self.iban = 'DE99999999999999999999'
        self.formatted_iban = 'DE99 9999 9999 9999 9999 99'
        self.user = 'Regina Phalange'
        self.filename = path_for_temp_file('{}.csv'.format(self.iban))

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

        super(ECImporterTestCase, self).tearDown()

    def _format_data(self, string, **kwargs):
        kwargs.update({
            'formatted_iban': self.formatted_iban,
            'header': HEADER,
            'iban': self.formatted_iban,
            'user': self.user,
        })
        return dedent(string).format(**kwargs).lstrip().encode('utf-8')

    def test_identify_correct(self):
        importer = ECImporter(self.iban, 'Assets:ING-DiBa:Extra', self.user)

        with open(self.filename, 'wb') as fd:
            fd.write(self._format_data('''
                Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                ;Letztes Update: aktuell

                IBAN;{formatted_iban}
                Kontoname;Extra-Konto
                Bank;ING-DiBa
                Kunde;{user}
                Zeitraum;01.06.2018 - 30.06.2018
                Saldo;5.000,00;EUR

                In der CSV-Datei finden Sie alle bereits gebuchten Umsätze. Die vorgemerkten Umsätze werden nicht aufgenommen, auch wenn sie in Ihrem Internetbanking angezeigt werden.

                {header}
                08.06.2018;08.06.2018;REWE Filialen Voll;Gutschrift;REWE SAGT DANKE;1.234,00;EUR;500,00;EUR
            '''))  # NOQA

        with open(self.filename) as fd:
            self.assertTrue(importer.identify(fd))

    def test_identify_invalid_iban(self):
        other_iban = 'DE00000000000000000000'

        with open(self.filename, 'wb') as fd:
            fd.write(self._format_data('''
                Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                ;Letztes Update: aktuell

                IBAN;{formatted_iban}
                Kontoname;Extra-Konto
                Bank;ING-DiBa
                Kunde;{user}
                Zeitraum;01.06.2018 - 30.06.2018
                Saldo;5.000,00;EUR

                In der CSV-Datei finden Sie alle bereits gebuchten Umsätze. Die vorgemerkten Umsätze werden nicht aufgenommen, auch wenn sie in Ihrem Internetbanking angezeigt werden.

                {header}
            '''))  # NOQA

        importer = ECImporter(other_iban, 'Assets:ING-DiBa:Extra', self.user)

        with open(self.filename) as fd:
            self.assertFalse(importer.identify(fd))

    def test_identify_invalid_user(self):
        other_user = 'Ken Adams'

        with open(self.filename, 'wb') as fd:
            fd.write(self._format_data('''
                Umsatzanzeige;Datei erstellt am: 25.07.2018 12:00
                ;Letztes Update: aktuell

                IBAN;{formatted_iban}
                Kontoname;Extra-Konto
                Bank;ING-DiBa
                Kunde;{user}
                Zeitraum;01.06.2018 - 30.06.2018
                Saldo;5.000,00;EUR

                In der CSV-Datei finden Sie alle bereits gebuchten Umsätze. Die vorgemerkten Umsätze werden nicht aufgenommen, auch wenn sie in Ihrem Internetbanking angezeigt werden.

                {header}
            '''))  # NOQA

        importer = ECImporter(self.iban, 'Assets:ING-DiBa:Extra', other_user)

        with open(self.filename) as fd:
            self.assertFalse(importer.identify(fd))
