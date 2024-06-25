from pysb.units import unitdefs
from pysb.units.core import *
from pysb.units.core import add_macro_units

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass

def set_molecule_volume(value: float, unit: str) -> None:
    unitdefs.set_molecule_volume(value, unit)
    return


__version__ = '0.3.0'