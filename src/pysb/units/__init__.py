from pysb.units import unitdefs
from pysb.units.core import *

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass

__version__ = '0.1.0'