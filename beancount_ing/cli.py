import sys
import tomllib
from pathlib import Path

from beangulp.testing import main as bg_main
from beancount_ing import ECImporter


def ec():
    config = _extract_config("ec")

    iban = config["iban"]
    account_name = config["account_name"]
    user = config["user"]
    file_encoding = config.get("file_encoding", "ISO-8859-1")

    importer = ECImporter(
        iban,
        account_name,
        user,
        file_encoding=file_encoding,
    )
    bg_main(importer)


def _extract_config(section: str):
    pyproject = Path("pyproject.toml")

    if not pyproject.exists():
        print("pyproject.toml not found. Please run from the root of the repo.")
        sys.exit(1)

    with pyproject.open("rb") as fd:
        config = tomllib.load(fd)

    config_section = config.get("tool", {}).get("beancount-ing", {}).get(section)

    if not config_section:
        print(f"tool.beancount-ing.{section} not found in pyproject.toml.")
        sys.exit(1)

    return config_section
