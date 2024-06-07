from . import unitdefs
from .core import *

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass