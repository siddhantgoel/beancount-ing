from contextlib import contextmanager
import csv
from datetime import datetime
from enum import Enum
import locale

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
def change_locale(key, value):
    original = locale.getlocale(key)

    try:
        locale.setlocale(key, value)
        yield
    finally:
        locale.setlocale(key, original)


class ECImporter(importer.ImporterProtocol):
    def __init__(self, iban, account, user, currency='EUR',
                 numeric_locale='de_DE.UTF-8', file_encoding='ISO-8859-1'):
        self.account = account
        self.user = user
        self.currency = currency
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
                key, value = line

                if key == 'Bank':
                    return value == 'ING-DiBa'

        return False

    def extract(self, file_):
        entries = []
        line_index = 0
        closing_balance_index = -1

        with change_locale(locale.LC_NUMERIC, self.numeric_locale):
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
                    key, value = line
                    line_index += 1

                    if key == 'IBAN':
                        if value != self.iban:
                            raise InvalidFormatError()
                    elif key == 'Bank':
                        if value != BANK:
                            raise InvalidFormatError()
                    elif key == 'Kunde':
                        if value != self.user:
                            raise InvalidFormatError()
                    elif key == 'Zeitraum':
                        splits = value.strip().split(' - ')

                        if len(splits) != 2:
                            raise InvalidFormatError()

                        self._date_from = datetime.strptime(
                            splits[0], '%d.%m.%Y').date()
                        self._date_to = datetime.strptime(
                            splits[1], '%d.%m.%Y').date()
                    elif key == 'Saldo':
                        self._balance = Amount(
                            locale.atof(value.rstrip(' EUR'), Decimal),
                            self.currency)
                        closing_balance_index = line_index

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
                reader = csv.DictReader(fd, delimiter=';',
                                        quoting=csv.QUOTE_MINIMAL,
                                        quotechar='"')

                for line in reader:
                    meta = data.new_metadata(file_.name, line_index)

                    amount = Amount(locale.atof(line['Betrag (EUR)'], Decimal),
                                    self.currency)
                    date = datetime.strptime(
                        line['Buchungstag'], '%d.%m.%Y').date()

                    if line['Verwendungszweck'] == 'Tagessaldo':
                        entries.append(
                            data.Balance(meta, date, self.account, amount,
                                         None, None)
                        )
                    else:
                        description = '{} {}'.format(
                            line['Buchungstext'],
                            line['Verwendungszweck']
                        )

                        postings = [
                            data.Posting(self.account, amount, None, None,
                                         None, None)
                        ]

                        entries.append(
                            data.Transaction(
                                meta, date, self.FLAG,
                                line['Auftraggeber / Begünstigter'],
                                description, data.EMPTY_SET, data.EMPTY_SET,
                                postings
                            )
                        )

                    line_index += 1

                # Closing Balance
                meta = data.new_metadata(file_.name, closing_balance_index)
                entries.append(
                    data.Balance(meta, self._date_to, self.account,
                                 self._balance, None, None)
                )

            return entries
