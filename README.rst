Beancount ING-DiBa Importer
===========================

.. image:: https://github.com/siddhantgoel/beancount-ing-diba/workflows/beancount-ing-diba/badge.svg
    :target: https://github.com/siddhantgoel/beancount-ing-diba/workflows/beancount-ing-diba/badge.svg

.. image:: https://img.shields.io/pypi/v/beancount-ing-diba.svg
    :target: https://pypi.python.org/pypi/beancount-ing-diba

.. image:: https://img.shields.io/pypi/pyversions/beancount-ing-diba.svg
    :target: https://pypi.python.org/pypi/beancount-ing-diba

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

:code:`beancount-ing-diba` provides an Importer for converting CSV exports of
`ING-DiBa`_ account summaries to the Beancount_ format.

Installation
------------

.. code-block:: bash

    $ pip install beancount-ing-diba

In case you prefer installing from the Github repository, please note that
:code:`master` is the development branch so :code:`stable` is what you should be
installing from.

Usage
-----

.. code-block:: python

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

.. _ING-DiBa: https://www.ing-diba.de/
.. _Beancount: http://furius.ca/beancount/
