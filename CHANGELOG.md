# CHANGELOG

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
