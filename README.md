# pysb-units

![Python version badge](https://img.shields.io/badge/python-3.11.3-blue.svg)
[![PySB version badge](https://img.shields.io/badge/PySB->%3D1.15.0-9cf.svg)](https://pysb.org/)
[![license](https://img.shields.io/github/license/Borealis-BioModeling/pysb-units.svg)](LICENSE)
![version](https://img.shields.io/badge/version-0.2.0-orange.svg)
[![release](https://img.shields.io/github/release-pre/Borealis-BioModeling/pysb-units.svg)](https://github.com/Borealis-BioModeling/pysb-units/releases/tag/v0.2.0)

`pysb-units` is an add-on for the [PySB](https://pysb.org/) modeling framework that provides tools to add units to models. 

## Table of Contents

 1. [Install](#install)
     1. [Dependencies](#dependencies)
     2. [pip install](#pip-install)
     3. [Manual install](#manual-install)
 2. [License](#license)
 3. [Change Log](#change-log)
 4. [Documentation and Usage](#documentation-and-usage)
     1. [Quick Overview](#quick-overview)
     2. [Example](#example)
     3. [List of macros](#list-of-macros)
     4. [Preconstructed models](#preconstructed-models)
 5. [Contact](#contact)
 6. [Citing](#citing)  
 7. [Other Useful Tools](#other-useful-tools)

------

# Install

| **! Note** |
| :--- |
|  psyb-units is still in version zero development so new versions may not be backwards compatible. |

**pysb-units** installs as the `pysb.units` Python (namespace) package. It is has been developed with Python 3.11.3 and PySB 1.15.0.

### Dependencies

Note that `pysb-units` has the following core dependencies:
   * [PySB](https://pysb.org/) - developed using version 1.15.0.
   * [astropy](https://www.astropy.org/) - developed using version 5.3.4.
   * [sympy](https://www.sympy.org/en/index.html) - developed using version 1.11.1. 


### pip install

You can install `pysb-units` version 0.2.0 with `pip` sourced from the GitHub repo:

##### with git installed:

Fresh install:
```
pip install git+https://github.com/Borealis-BioModeling/pysb-units@v0.2.0
```
Or to upgrade from an older version:
```
pip install --upgrade git+https://github.com/Borealis-BioModeling/pysb-units@v0.2.0
```
##### without git installed:

Fresh install:
```
pip install https://github.com/Borealis-BioModeling/pysb-units/archive/refs/tags/v0.2.0.zip
```
Or to upgrade from an older version:
```
pip install --upgrade https://github.com/Borealis-BioModeling/pysb-units/archive/refs/tags/v0.2.0.zip
```
### Manual install

First, download the repository. Then from the `pysb-units` folder/directory run
```
pip install .
```

------

# License

This project is licensed under the BSD 2-Clause License - see the [LICENSE](LICENSE) file for details

------

# Change Log

See: [CHANGELOG](CHANGELOG.md)

------

# Documentation and Usage

## Quick Overview

The key features of `pysb-units` are a new `Unit` object derived from pysb annotations, a new `SimulationUnits` object, and drop-in replacements for core model components, including `Model`, `Parameter`, `Expression`, `Rule`, `Initial`, and `Observable` that include new features to help manage units. Additionally, `pysb-units` defines a couple of useful utility functions, including the `unitize` and `check` functions, which make it easier to add units to model and run additional unit checks (such as unit consistency).   

### Example

A simple model with one degradation reaction:

* Regular pysb:
```python

from pysb import Model, Parameter, Monomer, Initial, Observable, Expression

# Initialize the PySB model:
Model()

# Monomer(s):
Monomer('protein')

# Model parameter(s):
# Initial concentration of protein
Parameter('protein_0', 0.5) # uM
# 1st-order rate parameter for the degradation
Parameter('k_deg', 0.1) # 1/s

# Initial concentration(s)
Initial(protein, protein_0)

# Reaction rule(s)
# Just the one degradation
Rule('degradation', protein() >> None, k_deg)

# Observables
# Time-dependent protein concentration:
Observable('protein_t', protein()) # uM

# Expressions
# The time-dependent degradation rate:
Expression('deg_rate', (protein_t * k_deg)) # uM/s

```

* pysb with pysb-units
```python
# Import the pysb components we need:
from pysb import Model, Parameter, Monomer, Initial, Observable, Expression
# Import pysb-units:
import pysb.units as units

# Activate units - replaces core model components
# with the appropriate versions from pysb.units:
units.unitize()

# Initialize the PySB model:
Model()

# The primary units needed for simulating the model are 
# concentration (or amount) and time. We can define those
# here with SimulationUnits:
SimulationUnits(concentration='uM', time='s')

# Monomer(s):
Monomer('protein')

# Model parameter(s):
# Initial concentration of protein:
Parameter('protein_0', 500.)
# Attach units to protein_0:
Unit(protein_0, 'nM')


# 1st-order rate parameter for the degradation
# defined with frequency (1/time) units - here, 
# we chain Unit and Parameter definitions:
Unit(Parameter('k_deg', 0.1), '1/s') 


# Initial concentration(s)
Initial(protein, protein_0)


# Reaction rule(s)
# Just the one degradation
Rule('degradation', protein() >> None, k_deg)

# Observables
# Time-dependent protein concentration:
Observable('protein_t', protein())

# Expressions
# The time-dependent degradation rate:
Expression('deg_rate', (protein_t * k_deg))

# Apply additional unit checks, including unit duplication
# and unit consistency checking:
units.check()

```

In the above unit-ed example, additional unit-based features and unit validation are applied:
 * `SimulationUnits(concentration='uM', time='s')` - sets the the expected units for the concentration (or amount) and time globally for the model. Any parameters that have concentration or time units will be checked against these definitions and if necessary automatically converted to the expected units.
 * `Unit(protein_0, 'nM')` - the unit 'nM' will be automatically converted to 'uM'since that is the global concentration unit we defined with `SimulationUnits`, and the appropriate scaling will be applied to `protein_0.value`. 
 * `Initial(protein, protein_0)` the units of `protein_0` will be checked to make sure they are a valid concentration. 
 * `Rule('degradation', protein >> None, k_deg)` the reaction order of the rule will be determined and the units of `k_deg` will be checked to make sure they match the expected unit type corresponding to that reaction order. In this case, the degradation is a 1st-order reaction, so `k_deg` is expected to have 
inverse time (i.e., frequency) units: [1 /  time], such as, [1 / s] or [1 / h].
 * `Observable('protein_t', protein())` - here, the units of the observable will be automatically inferred based on those set with `SimulationUnits`, so the observable will have units of 'uM'.
 * `Expression('deg_rate', (protein_t * k_deg))` - units of expressions are automatically inferred from the units of parameters and observables, so in this case the Expression will have units of 'uM/s'.
 * `units.check()` - this function applies additional unit checking and will issue warnings for duplicate units (two different units assigned to the same parameter), lack of consistency for units of the same physical type (e.g., concentration, time, etc.), and parameters without any 



## Using units with pysb.macros

PySB contains some helpful macro functions, such as `bind` and `degrade`, that can be used to streamline rule creation for recurring motifs. To use these macros with the `pysb.units` add-on you can use the `add_macro_units` function as below:

```python
# Import the pysb components we need:
from pysb import Model, Parameter, Monomer, Initial, Observable, Expression
# Import the module with the wanted macros:
from pysb import macros
# Import pysb-units:
import pysb.units as units

# Activate units - replaces core model components
# with the appropriate versions from pysb.units:
units.unitize()
# Apply the units to the macros module:
units.add_macro_units(macros)


# Initialize the PySB model:
Model()

# The core units used when simulating the model are 
# concentration (or amount) and time. We can define those
# here with SimulationUnits:
SimulationUnits(concentration='uM', time='s')

# Monomer(s):
Monomer('protein')

# Model parameter(s):
# Initial concentration of protein:
Parameter('protein_0', 500.)
# Attach units to protein_0:
Unit(protein_0, 'nM')


# 1st-order rate parameter for the degradation
# defined with frequency (1/time) units - here, 
# we chain Unit and Parameter definitions:
Unit(Parameter('k_deg', 0.1), '1/s') 


# Initial concentration(s)
Initial(protein, protein_0)


# Reaction rule(s)
# Just the one degradation - instead
# of defining a Rule that encodes the degradation reaction
# we can take advantage of degrade macro:
macros.degrade(protein(), k_deg)

# Observables
# Time-dependent protein concentration:
Observable('protein_t', protein())

# Expressions
# The time-dependent degradation rate:
Expression('deg_rate', (protein_t * k_deg))

# Apply additional unit checks, including unit duplication
# and unit consistency checking:
units.check()

```

## Custom Units

`pysb.units` leverages the `astropy.units` package for unit parsing and as its physical units library, but adds the following custom units/unit-types for reaction model use:

 * "M" = molar concentration : an alias for mole / L. Includes all fraction orders from femto to milli.
 * "1/cell" = number per cell : useful for stochastic simulations.
 * "1 / (cell**-1 * s)" = cellular reaction rate : reaction rate corresponding to concentrations in number per cell  
 * "mcg" = micrograms : alias for "ug", often used in pharmaceuticals.
 * "mole / m**2" = mole area density 
 * "g / s" = mass velocity : for reaction rates where mass is used in place of concentration.


------

# Contact

Please open a [GitHub Issue](https://github.com/Borealis-BioModeling/pysb-units/issues) to
report any problems/bugs or make any comments, suggestions, or feature requests.

------

# Citing

If this package is useful in your work, please cite in any publications:

```
Blake A. Wilson. (2024). pysb-units. (v0.2.0). https://github.com/Borealis-BioModeling/pysb-units
```

-----

# Other Useful Tools

## Parameter estimation

Please see packages such as [simplePSO](https://github.com/LoLab-MSM/simplePSO), [PyDREAM](https://github.com/LoLab-MSM/PyDREAM), [Gleipnir](https://github.com/LoLab-MSM/Gleipnir), or [GAlibrate](https://github.com/blakeaw/GAlibrate) for tools to do PySB model parameter estimation using stochastic optimization or Bayesian Monte Carlo approaches.

# PKPD modeling with PySB

If you want to build PKPD models with PySB the [pysb-pkpd](https://github.com/Borealis-BioModeling/psyb-pkpd) add-on can help.

## PD response models

If you want to separately fit response data independetly of PK data, then the [pharmacodynamic-response-models](https://github.com/NTBEL/pharmacodynamic-response-models) package may also be useful.  

## PySB model visualization

[pyvipr](https://github.com/LoLab-MSM/pyvipr) can be used for static and dynamic PySB model visualizations.

-----