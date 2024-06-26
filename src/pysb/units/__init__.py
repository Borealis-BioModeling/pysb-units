from pysb.units import unitdefs
from pysb.units.core import *
from pysb.units.core import add_macro_units

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass


__version__ = '0.3.0'