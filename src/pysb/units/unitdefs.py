"""Defines some custom units and unit physical types for biological models.
"""

import astropy.units as u

__all__: list[str] = []  #  Units are added at the end

# Namespace for defining new units.
_ns = globals()

# Prefixes to exclude for new unit definitions.
_exclude = [
    "Q",
    "R",
    "Y",
    "Z",
    "E",
    "P",
    "T",
    "G",
    "M",
    "k",
    "h",
    "da",
    "z",
    "y",
    "r",
    "q",
]

## Define new custom units ##

# Molar concentration (M)
u.def_unit(
    "M",
    u.mole / u.L,
    namespace=_ns,
    prefixes=True,
    doc="molar concentration (M)",
    exclude_prefixes=_exclude,
)

# Define a cell unit so users can define concentrations as
# number per cell (1 / cell), which is useful for stochastic simulations.
cell = u.def_unit("cell", namespace=_ns, doc="cell unit.")

# alias for micrograms commonly used for pharmaceuticals.
u.def_unit("mcg", u.ug, namespace=_ns, doc="alias for microgram (ug)")

# Define a molecules unit, also useful for stochastic sims:
molec = u.def_unit("molecules", namespace=_ns, doc='number of molecules')

## Define new custom physical types ##
# Cell unit
u.physical.def_physical_type(cell, "cell")
# Number per cell type
u.physical.def_physical_type(cell**-1, "number per cell")
# New reaction rate type for rates 1 / ( [number per cell] * [time])
u.physical.def_physical_type(cell / u.s, "cellular reaction rate")
# Ratio of mol / area is unknown phyical type by default, so let's define here:
u.physical.def_physical_type((u.mol / u.m**2), "mole area density")
# Ratio of g / s is unknown phyical type by default, so let's define here:
u.physical.def_physical_type((u.g / u.s), "mass velocity")
u.physical.def_physical_type(molec, "number of molecules")

# Get a list of physical types that could be used
# in defining concentrations.
# Unit patterns:
concentration_units = [
    M,
    u.g / u.m**3,
    u.g / u.m**2,
    cell**-1,
    u.mol / u.m**2,
    u.m**-3,
    u.m**-2,
    molec,
]
# Their physical types:
concentration_phys_types = [unit.physical_type for unit in concentration_units]

# Get a list of physical types that could be used
# in defining reaction rates.
# Unit patterns:
rate_units = [
    M / u.s,
    u.mol / u.s,
    u.g / u.s,
    u.m**-2 / u.s,
    u.m**-3 / u.s,
    cell**-1 * u.s**-1,
    molec * u.s**-1,
]
# Their physical types
rate_phys_types = [unit.physical_type for unit in rate_units]

# Define functions to check if physical type matches a 
# concentration or rate type:
def is_concentration(unit: u.Unit) -> bool:
    phys_type = unit.physical_type
    return (phys_type in concentration_phys_types)

def is_rate(unit: u.Unit) -> bool:
    phys_type = unit.physical_type
    return (phys_type in rate_phys_types)

def is_zero_order_rate_constant(unit: u.Unit) -> bool:
    return is_rate(unit)

def is_first_order_rate_constant(unit: u.Unit) -> bool:
    return ("frequency" == unit.physical_type)

def is_second_order_rate_constant(unit: u.Unit) -> bool:
    bases = unit.bases
    powers = unit.powers
    phys_types = [base.physical_type for base in bases]
    time_idx = None
    has_freq = False
    for i in range(len(bases)):
        if phys_types[i] == 'time':
            time_idx = i
            has_freq = ((bases[i]**powers[i]).physical_type == 'frequency')

    other_unit = None
    has_conc = False
    # Use a loop here in case the concentration unit is given as a 
    # a composite value like (mol / l)
    for i in range(len(bases)):
        if i != time_idx:
            if other_unit is None:
                other_unit = bases[i]**(-1 * powers[i])
            else:
                other_unit *= bases[i]**(-1 * powers[i])    
    if other_unit is not None:
        has_conc = is_concentration(other_unit)
    return (has_freq and has_conc)

 


# Physical type for zero order rate constants
# which are amount or concentration per second,
# e.g., M/s
k_zero_type = rate_phys_types
# Physical type for first order rate constants
# which are per second (1/s):
k_first_type = ["frequency"]
# Physical type for second order rate constants
# which are per amount or per concentration per second,
# e.g., 1 / (M s)


###########################################################################
# ALL & DOCSTRING

__all__ += [n for n, v in _ns.items() if isinstance(v, u.UnitBase)]

if __doc__ is not None:
    # This generates a docstring for this module that describes all of the
    # standard units defined here.
    from astropy.units.utils import generate_unit_summary as _generate_unit_summary

    __doc__ += _generate_unit_summary(globals())


def enable():
    """
    Enable Imperial units so they appear in results of
    `~astropy.units.UnitBase.find_equivalent_units` and
    `~astropy.units.UnitBase.compose`.

    This may be used with the ``with`` statement to enable Imperial
    units only temporarily.
    """
    # Local import to avoid cyclical import
    # Local import to avoid polluting namespace
    import inspect

    from astropy.units.core import add_enabled_units

    return add_enabled_units(inspect.getmodule(enable))
