"""Updated version of the pysb bngwiki_simple example model with units.

Units features are from the pysb-units add-on.

Adapted from:
https://github.com/pysb/pysb/blob/master/pysb/examples/bngwiki_simple.py
"""

from __future__ import print_function
from pysb import *
from pysb.units import units

# Define the model inside the units context for
# pysb.units features. This includes SimulationUnits and Unit objects and
# the set_molecule_volume function. Upon exiting the units context the
# pysb.units.check function is executed to evaluate any potential issues with
# the units, including checking for duplicate Unit objects, unit consistency,
# or potentially missing units).
with units():

    Model()

    # Simulation units - use concentration='molecules' for
    # molecule counts.
    SimulationUnits(concentration="molecules", time="s")

    # Physical and geometric constants
    Unit(Parameter("f", 0.01), None)  # scaling factor

    # Set the volume for molar concentrations to molecules
    set_molecule_volume(f.value * 100.0, "pL")

    # Initial concentrations
    Parameter("EGF0", 2.0, unit="nM")
    Parameter("EGFR0", f.value * 1.8e5, unit="molecules")

    # Rate constants
    Parameter("kp1", 9.0e7, unit="1/(M*s)")
    Parameter("km1", 0.06, unit="1/s")

    # Monomers
    Monomer("EGF", ["R"])
    Monomer("EGFR", ["L", "CR1", "Y1068"], {"Y1068": ["U", "P"]})

    # Initial conditions
    Initial(EGF(R=None), EGF0)
    Initial(EGFR(L=None, CR1=None, Y1068="U"), EGFR0)

    # Rules
    Rule("egf_binds_egfr", EGF(R=None) + EGFR(L=None) | EGF(R=1) % EGFR(L=1), kp1, km1)

    # Species LR EGF(R!1).EGFR(L!1)
    Observable("Lbound", EGF(R=ANY))  # Molecules


if __name__ == "__main__":
    print(__doc__, "\n", model)
    print(
        """
NOTE: This model code is designed to be imported and programatically
manipulated, not executed directly. The above output is merely a
diagnostic aid."""
    )
