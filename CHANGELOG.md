# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.2.0] - 2024-06-20

### Added
- `core.SimulationUnits` class that allows users to define global model units for concentration and time with auto conversion of parameters defined with relevant units. This included some additional logic in the `ParameterUnit.__init__` to check for an instance of `SimulationUnits` in the model and convert the units automatically as needed. Also a check in the `units.Observable` that auto assigns a unit based on `SimulationUnits`. 
- `convert` function to `ParameterUnit`.
- `core.molar_to_molecules` function that can convert a unit with a molar concentration to one with the number of molecules. 

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