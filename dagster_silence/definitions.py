# dagster_silence/definitions.py
from dagster import Definitions, load_assets_from_modules
from . import assets  # On importe ton fichier assets.py

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)