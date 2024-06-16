# pysb-units

![Python version badge](https://img.shields.io/badge/python-3.11.3-blue.svg)
[![PySB version badge](https://img.shields.io/badge/PySB->%3D1.15.0-9cf.svg)](https://pysb.org/)
[![license](https://img.shields.io/github/license/Borealis-BioModeling/pysb-units.svg)](LICENSE)
![version](https://img.shields.io/badge/version-0.1.0-orange.svg)
[![release](https://img.shields.io/github/release-pre/Borealis-BioModeling/pysb-units.svg)](https://github.com/Borealis-BioModeling/pysb-units/releases/tag/v0.1.0)

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
|  psyb-pkpd is still in version zero development so new versions may not be backwards compatible. |

**pysb-units** installs as the `pysb.pkpd` Python (namespace) package. It is has been developed with Python 3.11.3 and PySB 1.15.0.

### Dependencies

Note that `pysb-units` has the following core dependencies:
   * [PySB](https://pysb.org/) - developed using version 1.15.0.
   * [astropy](https://www.astropy.org/) - developed using version 5.3.4.
   * [sympy](https://www.sympy.org/en/index.html) - developed using version 1.11.1. 


### pip install

You can install `pysb-units` version 0.1.0 with `pip` sourced from the GitHub repo:

##### with git installed:

Fresh install:
```
pip install git+https://github.com/Borealis-BioModeling/pysb-units@v0.1.0
```
Or to upgrade from an older version:
```
pip install --upgrade git+https://github.com/Borealis-BioModeling/pysb-units@v0.1.0
```
##### without git installed:

Fresh install:
```
pip install https://github.com/Borealis-BioModeling/pysb-units/archive/refs/tags/v0.1.0.zip
```
Or to upgrade from an older version:
```
pip install --upgrade https://github.com/Borealis-BioModeling/pysb-units/archive/refs/tags/v0.1.0.zip
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

The key features of `pysb-units` are a new `Unit` object derived from pysb annotations with additional drop-in replacements for core model components, including `Model`, `Parameter`, `Expression`, `Rule`, and `Initial`, that include new features to help manage units.   

### Example

A simple model with one degradation reaction:

* Regular pysb:
```python

from pysb import Model, Parameter, Monomer, Initial

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
Rule('degradation', protein >> None, k_deg)

```
* pysb with pysb-units
```python

# Instead of importing model components from the core
# pysb package we can import the units module:
import pysb.units as units

# Initialize the PySB model:
units.Model()

# Monomer(s):
units.Monomer('protein')

# Model parameter(s):
# Initial concentration of protein
units.Parameter('protein_0', 500.)
# Attach a concentration unit to protein_0.
units.Unit(protein_0, 'nM', convert='uM')
# 1st-order rate parameter for the degradation
units.Parameter('k_deg', 0.1)
# Attach a frequency unit to k_deg.
units.Unit(k_deg, '1/s')

# Initial concentration(s)
units.Initial(protein, protein_0)

# Reaction rule(s)
# Just the one degradation
units.Rule('degradation', protein >> None, k_deg)

```

In the above example, using the united versions applies additional features and unit validation such as:
 * When providing the optional `convert` argument in `units.Unit(protein_0, 'nM', convert='uM')` the units are automatically converted from nM to uM with the appropriate scaling factor applied to the `protein_0` parameter value.
 * With `units.Initial(protein, protein_0)` the units of `protein_0` will be checked to make sure they are a valid concentration. 
 * With `units.Rule('degradation', protein >> None, k_deg)` the reaction order of the rule will be determined and the units of `k_deg`` will be checked to make sure they match the expected unit type corresponding to that reaction order. In this case, the degradation is a 1st-order reaction, so `k_deg`` is expected to have 
inverse time (i.e., frequency) units: [1 /  time], such as, [1 / s] or [1 / h].

## Additional unit consistency check

When defining a model you can call `check` function to evaluate unit consistency:

```python

# Instead of importing model components from the core
# pysb package we can import the units module:
import pysb.units as units

# Initialize the PySB model:
units.Model()

# Monomer(s):
units.Monomer('protein')

# Model parameter(s):
# Initial concentration of protein
units.Parameter('protein_0', 500.)
# Attach a concentration unit to protein_0.
units.Unit(protein_0, 'nM', convert='uM')
# 1st-order rate parameter for the degradation
units.Parameter('k_deg', 0.1)
# Attach a frequency unit to k_deg.
units.Unit(k_deg, '1/s')

# Initial concentration(s)
units.Initial(protein, protein_0)

# Reaction rule(s)
# Just the one degradation
units.Rule('degradation', protein >> None, k_deg)

# Check for unit-consistency and parameters without units.
units.check()
```

This will cause warning messages to be displayed for any non-matching units of the same physical type. E.g., if units of one rate parameter are `1/s` (per second) and another is `1/h` (per hour) a warning will issued to let the modeler know that these units are inconsistent. It will also check all model parameters and report any that have not been assigned units.

------

# Contact

Please open a [GitHub Issue](https://github.com/Borealis-BioModeling/pysb-units/issues) to
report any problems/bugs or make any comments, suggestions, or feature requests.

------

# Citing

If this package is useful in your work, please cite in any publications:

```
Blake A. Wilson. (2024). pysb-units. (v0.1.0). https://github.com/Borealis-BioModeling/pysb-units
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