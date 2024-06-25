# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.3.0] - 2024-06-25

### Added
- New units context manager function `core.units` that allows users to load unit-based functionality and then run checks using context `from pysb.units import units; with units():`. The context manager applies the `unitize` and `check` functions automatically so users don't need to do it manually. 

## [0.2.0] - 2024-06-20

### Added
- `core.SimulationUnits` class that allows users to define global model units for concentration and time with auto conversion of parameters defined with relevant units. This included some additional logic in the `ParameterUnit.__init__` to check for an instance of `SimulationUnits` in the model and convert the units automatically as needed. Also a check in the `units.Observable` that auto assigns a unit based on `SimulationUnits`. 
- `convert` function to `ParameterUnit`.
- `core.molar_to_molecules` function that can convert a unit with a molar concentration to one with the number of molecules. 
- `core.Unit` can accept `None` as an input in place of a unit string to explicity specify a unitless (i.e., dimensionless) quantity.
- `core.Expression.compose_units` function. 
- Custom equivalency in `unitdefs` for M to molecules with the `__init__.set_molecule_volume` and `unitdefs.set_molecule_volume` functions to allow the container volume used in the conversion to be updated by users. The `core.SimulationUnits` class can now handle auto conversions from molar concentrations to number of molecules for stochastic simulations. 

### Changed
- Updated the Documentation and Usage section of the README to streamline it a bit and add in the new `SimulationUnits` object.


### Fixed
- Error related to the definition of the cellular reaction rate physical type in `unitdefs`.
- Bug in a unit comparison in `core.check` when comparing units of the same physical type.


## [0.1.0] - 2024-06-14

### Added
- Initial development version of the package.

## [Unreleased] - yyyy-mm-dd

N/A

### Added

### Changed

### Fixed