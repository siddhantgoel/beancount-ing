# Beancount ING Importer

[![image](https://github.com/siddhantgoel/beancount-ing/workflows/beancount-ing/badge.svg)](https://github.com/siddhantgoel/beancount-ing/workflows/beancount-ing/badge.svg)

[![image](https://img.shields.io/pypi/v/beancount-ing.svg)](https://pypi.python.org/pypi/beancount-ing)

[![image](https://img.shields.io/pypi/pyversions/beancount-ing.svg)](https://pypi.python.org/pypi/beancount-ing)

[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`beancount-ing` provides an Importer for converting CSV exports of
[ING] (Germany) account summaries to the [Beancount] format.

## Installation

```sh
$ pip install beancount-ing
```

In case you prefer installing from the Github repository, please note that
`main` is the development branch so `stable` is what you should be installing
from.

## Usage

If you're not familiar with how to import external data into Beancount, please
read [this guide] first.

### Beancount 3.x

Beancount 3.x has replaced the `config.py` file based workflow in favor of having a
script based workflow, as per the [changes documented here]. The `beangulp` examples
suggest using a Python script based on `beangulp.Ingest`. Here's an example of how that
might work:


Add an `import.py` script in your project root with the following contents:

```python
from beancount_ing import ECImporter
from beangulp import Ingest

importers = (
    ECImporter(
        IBAN_NUMBER,
        "Assets:ING:EC",
        "Erika Mustermann",
        file_encoding="ISO-8859-1",
    ),
)

if __name__ == "__main__":
    ingest = Ingest(importer)
    ingest()
```

... and run it directly using `python import.py extract`.

### Beancount 2.x

Adjust your [config file] to include the provided `ECImporter`. A sample configuration
might look like the following:

```python
from beancount_ing import ECImporter

CONFIG = [
    # ...

    ECImporter(
        IBAN_NUMBER,
        "Assets:ING:EC",
        "Erika Mustermann",
        file_encoding="ISO-8859-1",
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

Please make sure you have Python 3.9+ and [Poetry] installed.

1. Clone the repository: `git clone https://github.com/siddhantgoel/beancount-ing`
2. Install the packages required for development: `poetry install`
3. That's basically it. You should now be able to run the test suite: `poetry
   run pytest tests/`.

[Beancount]: http://furius.ca/beancount/
[ING]: https://www.ing.de/
[Poetry]: https://python-poetry.org/
[changes documented here]: https://docs.google.com/document/d/1O42HgYQBQEna6YpobTqszSgTGnbRX7RdjmzR2xumfjs/edit#heading=h.hjzt0c6v8pfs
[config file]: https://beancount.github.io/docs/importing_external_data.html#configuration
[this guide]: https://beancount.github.io/docs/importing_external_data.html
