# Beancount ING-DiBa Importer

[![image](https://github.com/siddhantgoel/beancount-ing-diba/workflows/beancount-ing-diba/badge.svg)](https://github.com/siddhantgoel/beancount-ing-diba/workflows/beancount-ing-diba/badge.svg)

[![image](https://img.shields.io/pypi/v/beancount-ing-diba.svg)](https://pypi.python.org/pypi/beancount-ing-diba)

[![image](https://img.shields.io/pypi/pyversions/beancount-ing-diba.svg)](https://pypi.python.org/pypi/beancount-ing-diba)

[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`beancount-ing-diba` provides an Importer for converting CSV exports of
[ING-DiBa] (Germany) account summaries to the [Beancount] format.

## Installation

```sh
$ pip install beancount-ing-diba
```

In case you prefer installing from the Github repository, please note that
`develop` is the development branch so `stable` is what you should be installing
from.

## Usage

If you're not familiar with how to import external data into Beancount, please
read [this guide] first.

Adjust your [config file] to include the provided `ECImporter`. A sample
configuration might look like the following:

```python
from beancount_ing_diba import ECImporter

CONFIG = [
    # ...

    ECImporter(
        IBAN_NUMBER,
        'Assets:INGDiBa:EC',
        'Max Mustermann',
        file_encoding='ISO-8859-1',
    ),

    # ...
]
```

Once this is in place, you should be able to run `bean-extract` on the command
line to extract the transactions and pipe all of them into your Beancount file.

```sh
$ bean-extract /path/to/config.py transaction.csv >> you.beancount
```

## Contributing

Contributions are most welcome!

Please make sure you have Python 3.6+ and [Poetry] installed.

1. Clone the repository: `git clone https://github.com/siddhantgoel/beancount-ing-diba`
2. Install the packages required for development: `poetry install`
3. That's basically it. You should now be able to run the test suite: `poetry run py.test`.

[Beancount]: http://furius.ca/beancount/
[config file]: https://beancount.github.io/docs/importing_external_data.html#configuration
[ING-DiBa]: https://www.ing-diba.de/
[Poetry]: https://python-poetry.org/
[this guide]: https://beancount.github.io/docs/importing_external_data.html
