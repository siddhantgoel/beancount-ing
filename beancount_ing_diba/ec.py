import csv
from datetime import datetime
import re

from beancount.core.amount import Amount
from beancount.core import data
from beancount.core.number import Decimal
from beancount.ingest import importer


BANKS = ('ING', 'ING-DiBa')

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

META_KEYS = ('IBAN', 'Kontoname', 'Bank', 'Kunde', 'Zeitraum', 'Saldo')

PRE_HEADER = (
    'In der CSV-Datei finden Sie alle bereits gebuchten Umsätze. '
    'Die vorgemerkten Umsätze werden nicht aufgenommen, auch wenn sie in '
    'Ihrem Internetbanking angezeigt werden.'
)


class InvalidFormatError(Exception):
    pass


def _format_iban(iban):
    return re.sub(r'\s+', '', iban, flags=re.UNICODE)


def _format_number_de(value: str) -> Decimal:
    thousands_sep = '.'
    decimal_sep = ','

    return Decimal(value.replace(thousands_sep, '').replace(decimal_sep, '.'))


class ECImporter(importer.ImporterProtocol):
    def __init__(self, iban, account, user, file_encoding='ISO-8859-1'):
        self.iban = _format_iban(iban)
        self.account = account
        self.user = user
        self.file_encoding = file_encoding

        self._date_from = None
        self._date_to = None
        self._balance = None
        self._line_index = -1

    def file_account(self, _):
        return self.account

    def _is_valid_first_header(self, line):
        return line.startswith('Umsatzanzeige;Datei erstellt am')

    def _is_valid_second_header(self, line):
        return line == ';Letztes Update: aktuell'

    def identify(self, file_):
        with open(file_.name, encoding=self.file_encoding) as fd:

            def _read_line():
                return fd.readline().strip()

            # Header - first line
            line = _read_line()

            if not self._is_valid_first_header(line):
                return False

            # Header - second line
            line = _read_line()

            if not self._is_valid_second_header(line):
                return False

            # Empty line
            line = _read_line()

            if line:
                return False

            # Meta
            lines = [_read_line() for _ in range(len(META_KEYS))]

            reader = csv.reader(
                lines, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for line in reader:
                key, value, *_ = line

                if key == 'IBAN' and _format_iban(value) != self.iban:
                    return False

                if key == 'Bank' and value not in BANKS:
                    return False

                if key == 'Kunde' and value != self.user:
                    return False

        return True

    def extract(self, file_):
        entries = []
        self._line_index = 0

        def _read_line():
            line = fd.readline().strip()
            self._line_index += 1

            return line

        def _read_empty_line():
            line = _read_line()

            if line:
                raise InvalidFormatError()

        with open(file_.name, encoding=self.file_encoding) as fd:
            # Header - first line
            line = _read_line()

            if not self._is_valid_first_header(line):
                raise InvalidFormatError()

            # Header - second line
            line = _read_line()

            if not self._is_valid_second_header(line):
                raise InvalidFormatError()

            # Empty line
            _read_empty_line()

            # Meta
            lines = [_read_line() for _ in range(len(META_KEYS))]

            reader = csv.reader(
                lines, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for line in reader:
                key, *values = line
                self._line_index += 1

                if key == 'IBAN':
                    if _format_iban(values[0]) != self.iban:
                        raise InvalidFormatError()
                elif key == 'Bank':
                    if values[0] not in BANKS:
                        raise InvalidFormatError()
                elif key == 'Kunde':
                    if values[0] != self.user:
                        raise InvalidFormatError()
                elif key == 'Zeitraum':
                    splits = values[0].strip().split(' - ')

                    if len(splits) != 2:
                        raise InvalidFormatError()

                    self._date_from = datetime.strptime(
                        splits[0], '%d.%m.%Y'
                    ).date()
                    self._date_to = datetime.strptime(
                        splits[1], '%d.%m.%Y'
                    ).date()
                elif key == 'Saldo':
                    amount, currency = values

                    self._balance = Amount(_format_number_de(amount), currency)

            # Empty line
            _read_empty_line()

            # Pre-header line (or optional sorting line)
            line = _read_line()

            if line.startswith('Sortierung'):
                _read_empty_line()

                line = _read_line()

            if line != PRE_HEADER:
                raise InvalidFormatError()

            # Empty line
            _read_empty_line()

            # Data entries
            reader = csv.reader(
                fd, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for line in reader:
                if line == list(FIELDS):
                    continue

                (
                    date,  # Buchung
                    _,  # Valuta
                    payee,  # Auftraggeber/Empfänger
                    booking_text,  # Buchungstext
                    description,  # Verwendungszweck
                    _,  # Saldo
                    _,  # Währung
                    amount,  # Betrag
                    currency,  # Währung
                ) = line

                meta = data.new_metadata(file_.name, self._line_index)

                amount = Amount(_format_number_de(amount), currency)
                date = datetime.strptime(date, '%d.%m.%Y').date()

                description = '{} {}'.format(booking_text, description).strip()

                postings = [
                    data.Posting(self.account, amount, None, None, None, None)
                ]

                entries.append(
                    data.Transaction(
                        meta,
                        date,
                        self.FLAG,
                        payee,
                        description,
                        data.EMPTY_SET,
                        data.EMPTY_SET,
                        postings,
                    )
                )

                self._line_index += 1

        return entries
