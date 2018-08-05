from contextlib import contextmanager
import csv
from datetime import datetime
import locale
import re

from beancount.core.amount import Amount
from beancount.core import data
from beancount.core.number import Decimal
from beancount.ingest import importer


BANK = 'ING-DiBa'

FIELDS = (
    'Buchung',
    'Valuta',
    'Auftraggeber/Empfänger',
    'Buchungstext',
    'Verwendungszweck',
    'Saldo',
    'Währung',
    'Betrag',
    'Währung',
)

PRE_HEADER = (
    'In der CSV-Datei finden Sie alle bereits gebuchten Umsätze. '
    'Die vorgemerkten Umsätze werden nicht aufgenommen, auch wenn sie in '
    'Ihrem Internetbanking angezeigt werden.'
)


class InvalidFormatError(Exception):
    pass


@contextmanager
def _change_locale(key, value):
    original = locale.getlocale(key)

    try:
        locale.setlocale(key, value)
        yield
    finally:
        locale.setlocale(key, original)


def _format_iban(iban):
    return re.sub(r'\s+', '', iban, flags=re.UNICODE)


class ECImporter(importer.ImporterProtocol):
    def __init__(self, iban, account, user, numeric_locale='de_DE.UTF-8',
                 file_encoding='ISO-8859-1'):
        self.iban = _format_iban(iban)
        self.account = account
        self.user = user
        self.numeric_locale = numeric_locale
        self.file_encoding = file_encoding

        self._date_from = None
        self._date_to = None
        self._balance = None

    def file_account(self, _):
        return self.account

    def _is_valid_first_header(self, line):
        return line.startswith('Umsatzanzeige;Datei erstellt am')

    def _is_valid_second_header(self, line):
        return line == ';Letztes Update: aktuell'

    def identify(self, file_):
        with open(file_.name, encoding=self.file_encoding) as fd:
            # Header - first line
            line = fd.readline().strip()

            if not self._is_valid_first_header(line):
                return False

            # Header - second line
            line = fd.readline().strip()

            if not self._is_valid_second_header(line):
                return False

            # Empty line
            line = fd.readline().strip()

            if line:
                return False

            # Meta
            lines = [fd.readline().strip() for _ in range(6)]

            reader = csv.reader(lines, delimiter=';',
                                quoting=csv.QUOTE_MINIMAL, quotechar='"')

            for line in reader:
                key, value, *_ = line

                if key == 'IBAN' and _format_iban(value) != self.iban:
                    return False

                if key == 'Bank' and value != BANK:
                    return False

                if key == 'Kunde' and value != self.user:
                    return False

        return True

    def extract(self, file_):
        entries = []
        line_index = 0

        with _change_locale(locale.LC_NUMERIC, self.numeric_locale):
            with open(file_.name, encoding=self.file_encoding) as fd:
                # Header - first line
                line = fd.readline().strip()
                line_index += 1

                if not self._is_valid_first_header(line):
                    raise InvalidFormatError()

                # Header - second line
                line = fd.readline().strip()
                line_index += 1

                if not self._is_valid_second_header(line):
                    raise InvalidFormatError()

                # Empty line
                line = fd.readline().strip()
                line_index += 1

                if line:
                    raise InvalidFormatError()

                # Meta
                lines = [fd.readline().strip() for _ in range(6)]

                reader = csv.reader(lines, delimiter=';',
                                    quoting=csv.QUOTE_MINIMAL, quotechar='"')

                for line in reader:
                    key, *values = line
                    line_index += 1

                    if key == 'IBAN':
                        if _format_iban(values[0]) != self.iban:
                            raise InvalidFormatError()
                    elif key == 'Bank':
                        if values[0] != BANK:
                            raise InvalidFormatError()
                    elif key == 'Kunde':
                        if values[0] != self.user:
                            raise InvalidFormatError()
                    elif key == 'Zeitraum':
                        splits = values[0].strip().split(' - ')

                        if len(splits) != 2:
                            raise InvalidFormatError()

                        self._date_from = datetime.strptime(
                            splits[0], '%d.%m.%Y').date()
                        self._date_to = datetime.strptime(
                            splits[1], '%d.%m.%Y').date()
                    elif key == 'Saldo':
                        amount, currency = values

                        self._balance = Amount(locale.atof(amount, Decimal),
                                               currency)

                # Empty line
                line = fd.readline().strip()
                line_index += 1

                if line:
                    raise InvalidFormatError()

                # PreHeader line
                line = fd.readline().strip()
                line_index += 1

                if line != PRE_HEADER:
                    raise InvalidFormatError()

                # Empty line
                line = fd.readline().strip()
                line_index += 1

                if line:
                    raise InvalidFormatError()

                # Data entries
                reader = csv.reader(fd, delimiter=';',
                                    quoting=csv.QUOTE_MINIMAL,
                                    quotechar='"')

                for line in reader:
                    if line == list(FIELDS):
                        continue

                    (
                        date,           # Buchung
                        _,              # Valuta
                        payee,          # Auftraggeber/Empfänger
                        booking_text,   # Buchungstext
                        description,    # Verwendungszweck
                        _,              # Saldo
                        _,              # Währung
                        amount,         # Betrag
                        currency        # Währung
                    ) = line

                    meta = data.new_metadata(file_.name, line_index)

                    amount = Amount(
                        locale.atof(amount, Decimal), currency)
                    date = datetime.strptime(
                        date, '%d.%m.%Y').date()

                    description = '{} {}'.format(
                        booking_text,
                        description,
                    )

                    postings = [
                        data.Posting(self.account, amount, None, None,
                                     None, None)
                    ]

                    entries.append(
                        data.Transaction(
                            meta, date, self.FLAG,
                            payee,
                            description, data.EMPTY_SET, data.EMPTY_SET,
                            postings
                        )
                    )

                    line_index += 1

            return entries
