import csv
from datetime import datetime
import re

from beancount.core.amount import Amount
from beancount.core import data
from beancount.core.number import Decimal
from beancount.ingest import importer


BANKS = ('ING', 'ING-DiBa')

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
    def __init__(
        self, iban, account, user, file_encoding='ISO-8859-1',
    ):
        self.iban = _format_iban(iban)
        self.account = account
        self.user = user
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

            def _read_line():
                return fd.readline().strip()

            # Header - first line
            line = _read_line()

            if not self._is_valid_first_header(line):
                return False

            # Header - second line (optional)
            line = _read_line()

            if line:
                if not self._is_valid_second_header(line):
                    return False
                # Empty line
                line = _read_line() # this must be empty line

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

    def extract(self, file_, existing_entries=None):
        entries = []

        with open(file_.name, encoding=self.file_encoding) as fd:
            l = fd.readlines()

            # lines: array of dicts line number <n> and line content <s> { 'n' : <n>, 's': <s> }
            lines = [ { 'n':i+1, 's': l[i].strip() } for i in range(len(l)) ]
            metadata=[] # array of lines (no line number)
            transaction_data=[] # array of dicts (as lines above)
            for i in range(len(lines)):
                s = lines[i]['s']
                # skip empty line
                if not s:
                    continue
                if re.match(PRE_HEADER, s):
                    # end of metadata; read closing empty line and finish reading metadata
                    # transaction_data begins after an empty line
                    transaction_data = lines[i+2:]
                    break

                metadata.append(s)

            reader = csv.reader(
                metadata, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for line in reader:
                key, *values = line

                if key == '':
                    # no key: this is the ";Letztes Update: aktuell" line
                    pass
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
                elif key == 'Sortierung':
                    pass # sorting not yet processed

            if len(transaction_data) == 0 or not re.match('Buchung;Valuta;', transaction_data[0]['s']):
                # no transaction data or no column headers
                raise InvalidFormatError()

            # Prepend __lineno__ column
            transaction_data[0]['s'] = '__lineno__;' + transaction_data[0]['s']

            # for each consequent rows: prepend actual line number as a meta column
            for i in range(1, len(transaction_data)):
                transaction_data[i]['s'] = str(transaction_data[i]['n']) + ';' + transaction_data[i]['s']

            # Create transaction_lines list
            transaction_lines=[t['s'] for t in transaction_data]

            reader = csv.DictReader(
                transaction_lines, delimiter=';', quoting=csv.QUOTE_MINIMAL, quotechar='"'
            )

            for line in reader:
                date = line['Buchung']
                payee = line['Auftraggeber/Empfänger']
                booking_text = line['Buchungstext']
                description = line['Verwendungszweck']
                amount = line['Betrag']
                currency = line['Währung']

                meta = data.new_metadata(file_.name, line['__lineno__'])

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

        return entries
