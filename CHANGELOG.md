# CHANGELOG

## v1.0.1

- Remove support for Python 3.8

## v1.0.0

- Add Beancount 3.x support (thus removing Beancount 2.x support)
- Add `beancount-ing-ec` CLI command
- Rename `account` parameter to `account_name` (overlapping with the `account()` method
  definition required by `beangulp.importer.Importer`)
- Add Python 3.11 and 3.12 support
- Drop Python 3.7 support

## v0.6.0

- Rename to `beancount-ing`

## v0.5.0

- Generate `Balance` directives for opening / closing dates (thanks [@szabootibor])

## v0.4.1

- Handle duplicate "Währung" field name (thanks [@codedump] for the heads-up)
- Allow optional ";Letztes Update: aktuell" line in the header (thanks [@szabootibor])

## v0.4.0

- Support "Kategorie" field in the CSV downloads
- Enable support for Python 3.9
- Drop support for Python 3.5

## v0.3.1

- Update `extract` interface

## v0.3

- Support Python 3.8

## v0.2.1

- Support optional sorting line before the pre-header

## v0.2

- Replace `locale` based parsing of numbers with a simple helper function
  specifically for handling German formatting of numbers

## v0.1.2

- Allow multiple values for the `Bank` metadata field

## v0.1.1

- Remove incorrect `beancount.core.data.Balance` directive from extracted
  transactions

## v0.1

- Initial release

[@codedump]: https://github.com/codedump
[@szabootibor]: https://github.com/szabootibor
