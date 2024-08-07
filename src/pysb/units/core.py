"""Defines the Unit and SimulationUnits objects along with drop-in replacements for other model components.
"""

import weakref
import warnings
from contextlib import contextmanager
import sympy
from pysb.core import SelfExporter
import pysb
import astropy.units as u
from astropy.constants import N_A
from abc import ABC
from pysb.units import unitdefs

# Define __all__

__all__ = [
    "units",
    "Unit",
    "SimulationUnits",
    "Model",
    "Parameter",
    "Expression",
    "Initial",
    "Rule",
    "Observable",
    "Monomer",
    "Compartment",
    "ANY",
    "WILD",
    "Annotation",
    "check",
    "unitize",
    "set_molecule_volume",
]

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass

## Drop-ins for model components with added units features. ##


class Model(pysb.Model):
    """PySB model with additiional units features.

    This object is a subclass of pysb.core.Model that adds three new
    properties to the Model object that help with managing units defined in the
    the models.

    Added Properties:
        units (list) - a list of pysb.units.Unit objects defined for the given
            model.
        unit_map (dict) - a dictionary of unit strings keyed to the name of their
            respective model components.
        reaction_order (list(list)) - a list of model Rules and the corresponding
            reaction orders of their forward and reverse reactions: items are
            [Rule, Order of Forward Reaction, Order of Reverse Reaction].

    pysb.core.Model:
    """

    __doc__ += pysb.Model.__doc__

    @property
    def units(self) -> list:
        """List of Unit objects defined for this model."""
        unit_list = []
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_list.append(annotation)
        return unit_list

    @property
    def unit_map(self) -> dict:
        """Dictionary of model components (by name) with associated units."""
        unit_dict = dict()
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_dict[annotation.subject.name] = annotation.object
        return unit_dict

    @property
    def reaction_order(self) -> list:
        """List of model rules and their forward and reverse reaction orders."""
        orders = list()
        for rule in self.rules:
            order_forward = len(rule.reactant_pattern.complex_patterns)
            order_reverse = None
            if rule.is_reversible:
                order_reverse = len(rule.product_pattern.complex_patterns)

            orders.append([rule, order_forward, order_reverse])
        return orders


class Parameter(pysb.Parameter):
    """PySB model parameter component with additiional units features.

    This object is a subclass of pysb.core.Parameter. It adds two new attributes and one new
    property to the Parameter component that help with managing units defined in the
    the models, as well as updating the initialization and string representations of the
    Parameter component.

    Added Attributes:
        units (pysb.units.Unit) - The associated Unit object. Defaults to None.
        has_units (bool) - Does the parameter have units. Defaults to False.

    Added Properties:
        unit (list) - a list of pysb.units.Unit objects defined for the given
            model.
        unit_map (dict) - a dictionary of unit strings keyed to the name of their
            respective model components.
        reaction_order (list(list)) - a list of model Rules and the corresponding
            reaction orders of their forward and reverse reactions: items are
            [Rule, Order of Forward Reaction, Order of Reverse Reaction].

    """

    # __doc__ += pysb.Parameter.__doc__

    def __new__(
        cls, name, value=0.0, unit=None, _export=True, nonnegative=True, integer=False
    ):
        return super(pysb.Parameter, cls).__new__(
            cls, name, real=True, nonnegative=nonnegative, integer=integer
        )

    def __init__(
        self,
        name: str,
        value: float = 0.0,
        unit: str | None = None,
        _export: bool = True,
        nonnegative: bool = True,
        integer: bool = False,
    ):
        """Initialize a the Parameter component.

        Uses super to call the pysb.core.Parameter initialization and then sets
        the units and has_units attributes to default values (None, False).

        Args:
            name (str): Name of the parameter.
            value (float, optional): Numeric value of the parameter. Defaults to 0.0.
            _export (bool, optional): Should the componenet be exported. Defaults to True.
            nonnegative (bool, optional): Is the parameter value nonnegative. Defaults to True.
            integer (bool, optional): Is the parameter value an integer. Defaults to False.

        """

        super().__init__(name, value, _export, nonnegative, integer)
        self.units = None
        self.has_units = False
        if unit is not None:
            Unit(self, unit)
        return

    def __repr__(self):
        """Updated representation that displays any assigned units."""
        if self.has_units:
            return "%s(%s, %s), unit=[%s]" % (
                self.__class__.__name__,
                repr(self.name),
                repr(self.value),
                repr(self.units.value),
            )
        else:
            return super().__repr__()

    @property
    def unit(self):
        """Associated astropy.units.Unit object."""
        return self.units.unit


class Expression(pysb.Expression):
    """PySB model expression component with additiional units features.

    This object is a subclass of pysb.core.Expression.

    Overloads:
        __init__
        __repr__

    Added Attributes:
        units (pysb.units.Unit) - The associated Unit object.
        has_units (bool) - Does the expression have units. Defaults to False.

    """

    def __init__(self, name, expr, _export=True):
        """Initialize the Expression component.

        Uses super to call the pysb.core.Expression initialization and then sets
        the units and has_units attributes to default values (None, False) before
        initializing a new Unit object that will alter their values.

        Args:
            name (str): Name of the expression.
            expr (sympy expression): The corresponding expression. Defaults to 0.0.
            _export (bool, optional): Should the componenet be exported. Defaults to True.
        """

        unit_string, obs_pattern = self._compose_units(expr)
        # print(unit_string, obs_string)
        super().__init__(name, expr, _export=_export)
        self.units = None
        self.has_units = False
        expr_unit = Unit(self, unit_string, obs_pattern=obs_pattern)
        return

    def __repr__(self):
        """Updated representation that displays any assigned units."""
        base_repr = super().__repr__()
        if self.has_units:
            unit_repr = base_repr + ", unit=[{}]".format(self.units.value)
            # if self.obs_pattern is not None:
            #     unit_repr = base_repr + ", unit=[{}".format(self.units.value)+ " * unit({})]".format(self.obs_pattern)
            return unit_repr
        else:
            return base_repr

    @staticmethod
    def _compose_units(expr):
        """Composes the units of an expression from constituent components."""
        subs = []
        subs_uni = []
        subs_obs = []
        for a in expr.atoms():
            if isinstance(a, Expression):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
                # else:
                #     subs.append((a, 1))
                #     subs_uni.append((a, 1))
            elif isinstance(a, Parameter):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
                # else:
                #     subs.append((a, 1))
                #     subs_uni.append((a, 1))
            elif isinstance(a, Observable):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
                else:
                    subs_obs.append([a, 1])           
        unit_obs_expr = expr.subs(subs)
        unit_expr = unit_obs_expr.subs(subs_obs)
        obs_expr = expr.subs(subs_uni)
        unit_string = repr(unit_expr)
        try:
            # Fails if the resulting unit_string
            # is actually an unitless ratio such as '1/2'.
            expr_unit = u.Unit(unit_string)
        except:
            # In which case, we set the unit_string to "1"
            # to indicate a unitless quantity.
            unit_string = "1"
        if len(subs_obs) > 0:
            if isinstance(obs_expr, Observable):
                obs_string = repr(obs_expr.name)
            else:
                obs_string = repr(obs_expr)
        else:
            obs_string = None
        return unit_string, obs_string

    def compose_units(self):
        """Retuns the composed units of an expression from its constituent components."""
        return self._compose_units(self)


class Observable(pysb.Observable):

    def __init__(self, *args, **kwargs):
        self.units = None
        self.has_units = False
        super().__init__(*args, **kwargs)
        # If the global concentration units have been set with a SimulationUnits
        # object then we just infer the units of the observable as those concentration
        # units.
        if hasattr(SelfExporter.default_model, "simulation_units"):
            Unit(self, SelfExporter.default_model.simulation_units.concentration)

    def __repr__(self):
        ret = super().__repr__()
        if self.has_units:
            ret += ", unit=[" + self.units.value + "]"
        return ret


class Initial(pysb.Initial):

    def __init__(self, pattern, value, fixed=False, _export=True):
        if isinstance(value, (Parameter, Expression)):
            if value.has_units:
                is_conc_unit = unitdefs.is_concentration(value.units.unit)
                if not is_conc_unit:
                    msg = "Parameter or Expression '{}' with units '{}' passed to Initial doesn't have a recognized concentration unit pattern.".format(
                        value.name,
                        value.units.value,
                    )
                    unit_strings = [
                        uni.to_string() for uni in unitdefs.concentration_units
                    ]
                    msg += "\n Recognized concentration unit patterns include: \n {}".format(
                        unit_strings
                    )
                    raise WrongUnitError(msg)
        super().__init__(pattern, value, fixed, _export)
        self.units = None
        self.has_units = False
        if isinstance(value, Parameter):
            self.units = value.units
            self.has_units = value.has_units
        return

    def __repr__(self):
        ret = super().__repr__()
        if self.has_units:
            ret += ", unit=[" + self.units.value + "]"
        return ret


class Rule(pysb.Rule):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     self._validate_units()
    #     return

    def __init__(
        self,
        name,
        rule_expression,
        rate_forward,
        rate_reverse=None,
        delete_molecules=False,
        move_connected=False,
        energy=False,
        total_rate=False,
        _export=True,
    ):
        if not isinstance(rule_expression, pysb.RuleExpression):
            raise Exception("rule_expression is not a RuleExpression object")
        pysb.validate_expr(rate_forward, "forward rate")
        if rule_expression.is_reversible:
            pysb.validate_expr(rate_reverse, "reverse rate")
        elif rate_reverse:
            raise ValueError(
                "Reverse rate specified, but rule expression is "
                "not reversible. Use | instead of >>."
            )
        self.rule_expression = rule_expression
        self.reactant_pattern = rule_expression.reactant_pattern
        self.product_pattern = rule_expression.product_pattern
        self.is_reversible = rule_expression.is_reversible
        self.rate_forward = rate_forward
        self.rate_reverse = rate_reverse
        self.delete_molecules = delete_molecules
        self.move_connected = move_connected
        self.energy = energy
        self.total_rate = total_rate
        # Check synthesis products are concrete
        if self.is_synth():
            rp = self.reactant_pattern if self.is_reversible else self.product_pattern
            for cp in rp.complex_patterns:
                if not cp.is_concrete():
                    raise ValueError(
                        "Product {} of synthesis rule {} is not "
                        "concrete".format(cp, name)
                    )

        # Check the units of rate parameters
        if not self.energy:
            self._validate_units()

        pysb.Component.__init__(self, name, _export)

        # Get tags from rule expression
        tags = set()
        for rxn_pat in (
            rule_expression.reactant_pattern,
            rule_expression.product_pattern,
        ):
            if rxn_pat.complex_patterns:
                for cp in rxn_pat.complex_patterns:
                    if cp is not None:
                        if cp._tag:
                            tags.add(cp._tag)
                        tags.update(
                            mp._tag for mp in cp.monomer_patterns if mp._tag is not None
                        )

        # Check that tags defined in rates are used in the expression
        tags_rates = self._check_rate_tags("forward", tags) + self._check_rate_tags(
            "reverse", tags
        )

        missing = tags.difference(set(tags_rates))
        if missing:
            names = [t.name for t in missing]
            warnings.warn(
                'Rule "{}": Tags {} defined in rule expression but not used in '
                "rates".format(self.name, ", ".join(names)),
                UserWarning,
            )

    def _validate_units(self):

        def check_order(reaction_order, parameter):
            unit = parameter.units.unit
            if reaction_order == 0:
                return unitdefs.is_zero_order_rate_constant(unit)
            elif reaction_order == 1:
                return unitdefs.is_first_order_rate_constant(unit)
            elif reaction_order == 2:
                return unitdefs.is_second_order_rate_constant(unit)
            else:
                return False

        # If the rule is reversible, check that both
        # rate parameters have units.
        if self.is_reversible:
            if not (self.rate_forward.has_units and self.rate_reverse.has_units):
                err = "Both rate parameters must have defined units in reversible Rule definitions:\n"
                if self.rate_forward.has_units:
                    err += "Forward rate parameter '{}' has units '{}', but Reverse rate parameter '{}' lacks units.".format(
                        self.rate_forward.name,
                        self.rate_forward.units.value,
                        self.rate_reverse.name,
                    )

                else:
                    err += "Reverse rate parameter '{}' has units '{}', but Forward rate parameter '{}' lacks units.".format(
                        self.rate_reverse.name,
                        self.rate_reverse.units.value,
                        self.rate_forward.name,
                    )
                raise MissingUnitError(err)

        # Check the forward rate constant
        if self.rate_forward.has_units:
            reaction_order = len(self.reactant_pattern.complex_patterns)
            parameter = self.rate_forward
            if not check_order(reaction_order, parameter):
                err = "The rate parameter '{}' with units '{}' for the forward reaction with order {} doesn't have the correct unit pattern for that reaction order.".format(
                    parameter.name, parameter.units.value, reaction_order
                )
                raise WrongUnitError(err)
        if (self.is_reversible) and (self.rate_reverse.has_units):
            reaction_order = len(self.product_pattern.complex_patterns)
            parameter = self.rate_reverse
            if not check_order(reaction_order, parameter):
                err = "The rate parameter '{}' with units '{}' for the reverse reaction with order {} doesn't have the correct unit pattern for that reaction order.".format(
                    parameter.name, parameter.units.value, reaction_order
                )
                raise WrongUnitError(err)
        return

        # reaction_order =
        return


## Alias the model components that don't have any changes - just for convenience
Monomer = pysb.Monomer
Compartment = pysb.Compartment
ANY = pysb.ANY
WILD = pysb.WILD
Annotation = pysb.Annotation

## New Unit class ##

# class BaseUnit(metaclass=u.Unit):

#     def __init__(self, unit_string):
#         try:
#             super().__init__(unit_string)
#         except:
#             raise UnknownUnitError(
#                 "Unrecognizable unit pattern '{}'".format(unit_string)
#             )
#         return

# class UnitBase(ABC, pysb.Annotation):
#     pass


@contextmanager
def units():
    """Context manager for units."""
    try:
        # Requires depth of 3
        # 1 - back is inside try
        # 2 - back is in the units function
        # 3 - back is in the model namespace
        unitize(depth=3)
        yield

    finally:
        check()


def molar_to_molecules(self, unit: u.Unit, vol: float = 1.0) -> tuple[float, u.Unit]:
    """Converts a unit with molar concentration to one with number of molecules.

    Note: molecules = M * L * N_L
    E.g.: M/s -> molecules/s

    Args:
        unit (u.Unit): The unit.
        vol (float, optional): Container volume in L for the conversion. Defaults to 1.0.

    Returns:
        tuple[float, u.Unit]: conversion factor, updated molecules unit
    """
    # Check the unit as a composite for a molar concentration
    # signature
    if unit.physical_type == "molar concentration":
        return ((unit.to("M") * u.Unit("mol/L")) * vol * u.L * N_A).value, u.Unit(
            "molecules"
        )
    # Break the unit apart and check piece
    bases = unit.bases
    powers = unit.powers
    convert_to = u.Unit()
    for base, power in zip(bases, powers):
        if base.physical_type == "molar concentration":
            convert_to *= (
                (unit.to("M") * u.Unit("mol/L") * vol * u.L * N_A).value
                * u.Unit("moelcules")
            ) ** power
        else:
            convert_to *= base**power
    return convert_to.value, convert_to.unit


class SimulationUnits(object):
    """Primary model units used for simulations.

    Properties (read-only):
        time (str) - string representation of the time unit.
        concentration (str) - string representation of the concentration unit.
        frequency (str) - string representation of the frequency unit (1/time).
        time_unit (astropy.units.Unit) - The corresponding astropy Unit object
            for the time unit.
        concentration_unit (astropy.units.Unit) - The corresponding astropy Unit
            object for the concentration unit.
        frequency_unit (astropy.units.Unit) - The corresponding astropy Unit object
            for the frequency unit (1/time).
    """

    def __init__(
        self, concentration: str = "uM", time: str = "s", volume: str | None = None
    ):
        """Initializes the SimulationUnits object with input concentration and time units, and optional volume units.

        Args:
            concentration (str, optional): The concentration unit. Defaults to "uM".
            time (str, optional): The time unit. Defaults to "s".
            volume (str or None, optional): The volume unit. Defaults to None.

        Raises:
            UnknownUnitError: If concentration can't be parsed into a recognizable unit.
            WrongUnitError: If concentration unit isn't recognized as a concentration pattern.
            UnknownUnitError: If time can't be parsed into a recognizable unit.
            WrongUnitError: If time isn't recognized as a physical type of time.
        """
        try:
            self._concentration_unit = u.Unit(concentration)
        except:
            raise UnknownUnitError(
                "Unrecognizable concentration unit pattern '{}'".format(concentration)
            )
        if not unitdefs.is_concentration(self._concentration_unit):
            msg = "Concentration unit pattern '{}' isn't a recognized concentration pattern.".format(
                concentration
            )
            raise WrongUnitError(msg)
        try:
            self._time_unit = u.Unit(time)
        except:
            raise UnknownUnitError("Unrecognizable time unit pattern '{}'".format(time))
        if not (self._time_unit.physical_type == "time"):
            msg = "Time unit pattern '{}' isn't a recognized time pattern.".format(time)
            raise WrongUnitError(msg)
        if volume is not None:
            try:
                self._volume_unit = u.Unit(volume)
            except:
                raise UnknownUnitError(
                    "Unrecognizable volume unit pattern '{}'".format(volume)
                )

        self._concentration = concentration
        self._time = time
        self._frequency_unit = self._time_unit ** (-1)
        self._volume = volume
        setattr(SelfExporter.default_model, "simulation_units", self)
        self._model = weakref.ref(SelfExporter.default_model)
        return

    def __repr__(self) -> str:
        if self._volume is None:
            return "SimulationUnits(concentration='{}', time='{}')".format(
                self.concentration, self.time
            )
        else:
            return "SimulationUnits(concentration='{}', time='{}', volume='{}')".format(
                self.concentration, self.time, self.volume,
            )
    @property
    def time(self) -> str:
        """The time unit as a string."""
        return self._time

    @property
    def concentration(self) -> str:
        """The concentration unit as a string."""
        return self._concentration

    @property
    def frequency(self) -> str:
        """The frequency (1/time) unit as a string."""
        return self._frequency_unit.to_string()
    
    @property
    def volume(self) -> str:
        """The volume unit as a string or None."""
        return self._volume
    
    @property
    def time_unit(self) -> u.Unit:
        """The astropy.units.Unit representation of the time unit."""
        return self._time_unit

    @property
    def concentration_unit(self) -> u.Unit:
        """The astropy.units.Unit representation of the concentration unit."""
        return self._concentration_unit

    @property
    def frequency_unit(self) -> u.Unit:
        """The astropy.units.Unit representation of the frequency (1/time) unit."""
        return self._frequency_unit

    @property
    def volume_unit(self) -> u.Unit:
        """The astropy.units.Unit representation of the volume unit."""
        if self._volume is not None:
            return self._volume_unit
        else:
            return None
    # def _update_all(self):
    #     for unit in self._model.units:
    #         astro_unit = unit.unit
    #         bases = astro_unit.bases
    #         powers = astro_unit.powers
    #         new_unit = None
    #         for base, power in zip(bases, powers):
    #             if is_concentration(base):

    def convert_unit(self, unit: u.Unit) -> u.Unit:
        """Creates a new unit object with concentration and time units replaced with their pre-defined units.

        Args:
            unit (u.Unit): The input Unit object.

        Returns:
            u.Unit: What the input object is converted to.
        """
        # Check the unit as a composite for a concentration
        # signature.
        if unitdefs.is_concentration(unit):
            return self.concentration_unit
        # Break the unit apart and check piece
        bases = unit.bases
        powers = unit.powers
        convert_to = u.Unit()
        for base, power in zip(bases, powers):
            if unitdefs.is_concentration(base):
                convert_to *= self.concentration_unit**power
            elif base.physical_type == "time":
                convert_to *= self.time_unit**power
            elif (base.physical_type == "volume") and (self._volume is not None):
                convert_to *= self.volume_unit**power
            else:
                convert_to *= base**power
        return convert_to


# TODO: Refactor the Unit classes.
# Create a base class for the ParameterUnit, ExpressionUnit, and ObservableUnit objects,
# so that ParameterUnit doesn't need to be used as the base for ExpressionUnit and ObservableUnit.
# Taking advantage of the Annotation attributes for subject and object should allow some
# streamlining and removal of the specific privates like ParameterUnit._param and
# ExpressionUnit._expr.


class ParameterUnit(pysb.Annotation):
    """Add unit annotation to Parameter components.

    This subclass of the pysb.annotation.Annotation is only meant to be used
    internally for additional subclassing.

    Attributes:
      value (str): String representation of the units.
      unit (astropy.units.Unit): Astropy Unit object version of the units.
      expr (sympy.Symbol): sympy-based symbolic representation of the units.
    """

    def __init__(
        self, parameter: Parameter, unit_string: str | None, convert: str | None = None
    ):
        """

        Args:
            parameter : The Parameter to which we want to add units.
            unit_string : String representation of the units. If None, will be set 1 for
                dimensionless.
            convert (optional): String representation of another unit to which we want to convert unit_string. Defaults to None.

        Raises:
            ValueError: If parameter is not an instance of Parameter.
            UnknownUnitError: If unit_string can't be parsed into a known unit/defined unit.
            UnknownUnitError: If convert can't be parsed into a known unit/defined unit.
            ValueError: If the conversion from unit_string to convert fails.
        """
        if not isinstance(parameter, Parameter):
            raise ValueError(
                "ParameterUnit can only be assigned to Parameter component."
            )
        unit_string = self._check_dimensionless(unit_string)
        self._unit_string = unit_string
        self._param = parameter
        try:
            self._unit = u.Unit(unit_string)
            self._unit_string_parsed = self._unit.to_string()
        except:
            raise UnknownUnitError(
                "Unrecognizable unit pattern '{}'".format(unit_string)
            )
        if hasattr(SelfExporter.default_model, "simulation_units") and (
            unit_string != "1"
        ):
            # Check for complex units that contain time or concentration parts
            convert_unit = SelfExporter.default_model.simulation_units.convert_unit(
                self._unit
            )
            convert = convert_unit.to_string()
        if convert is not None:
            self.convert(convert)
        super().__init__(parameter, self._unit_string, predicate="units")
        self.name = "unit_" + parameter.name
        parameter.units = self
        parameter.has_units = True
        return

    @staticmethod
    def _check_dimensionless(unit_string):
        if unit_string is None:
            unit_string = "1"
        return unit_string

    def convert(self, new_unit: str):
        """Converts a the units.

        Args:
            new_unit (str): The new unit.

        Raises:
            UnknownUnitError: If new_unit can't be parsed into a recognized unit.
            ValueError: If the original unit can't be converted into new_unit.
        """
        unit_string = self._unit_string
        try:
            unit_orig = self.unit
            try:
                unit_new = u.Unit(new_unit)
            except:
                raise UnknownUnitError(
                    "Unrecognizable unit pattern '{}' for convert.".format(new_unit)
                )
            try:
                # Try a direct conversion
                conversion_factor = unit_orig.to(unit_new)
            except:
                try:
                    # Failed, now try breaking them apart and do piece by piece
                    # This should work for cases where we need to convert molar
                    # concentrations to molecules in complex unit patterns.
                    bases = unit_orig.bases
                    powers = unit_orig.powers
                    bases_new = unit_new.bases
                    powers_new = unit_new.powers
                    conversion_factor = 1.0
                    n_parts = len(bases)

                    for i in range(n_parts):
                        conversion_factor *= (bases[i].to(bases_new[i])) ** powers[i]
                except:
                    raise UnitConversionError(
                        "Unable to convert units {} to {}".format(unit_string, new_unit)
                    )

            self._param.value *= conversion_factor
            self._unit = unit_new
            self._unit_string = new_unit
            self._unit_string_parsed = unit_new.to_string()
        except:
            raise UnitConversionError(
                "Unable to convert units {} to {}".format(unit_string, new_unit)
            )

    # TODO:
    # Function that can change the unit assigned to a component.
    def _change_unit(self, unit_string):
        pass

    @property
    def value(self) -> str | None:
        """The string representation of the units."""
        if self._unit_string == "1":
            return None
        else:
            return self._unit_string

    @property
    def unit(self) -> u.Unit:
        """The astropy.units.Unit object represneting the units."""
        return self._unit

    def __repr__(self):
        repr_string = super().__repr__()
        split = repr_string.split(",")
        print(split)
        # Check for dimensionless:
        if split[1] == " '1'":
            return "%s,  None)" % (split[0])
        return "%s, %s)" % (split[0], split[1])

    @property
    def expr(self):
        """A sympy-based symbolic version of the units."""
        unit_bases = self.unit.bases
        unit_powers = self.unit.powers
        unit_symbols = [sympy.Symbol(base.to_string()) for base in unit_bases]
        return sympy.Mul(*[a**b for a, b in zip(unit_symbols, unit_powers)])

    @property
    def physical_type(self):
        return self.unit.physical_type


class ExpressionUnit(ParameterUnit):

    def __init__(
        self,
        expression: Expression,
        unit_string: str | None,
        obs_pattern: str | None = None,
    ):
        if not isinstance(expression, Expression):
            raise ValueError(
                "ExpressionUnit can only be assigned to Expression component."
            )
        unit_string = self._check_dimensionless(unit_string)
        self._unit_string = unit_string
        try:
            self._unit = u.Unit(unit_string)
            self._unit_string_parsed = self._unit.to_string()
        except:
            raise UnknownUnitError(
                "Unrecognizable unit pattern '{}'".format(unit_string)
            )
        if obs_pattern is not None:
            unit_obs = u.def_unit("unit({})".format(obs_pattern))
            self._unit *= unit_obs
            self._unit_string = self._unit.to_string()
        self._expr = expression
        super(ParameterUnit, self).__init__(
            expression, self._unit_string, predicate="units"
        )
        self.name = "unit_" + expression.name
        expression.units = self
        expression.has_units = True
        return


class ObservableUnit(ParameterUnit):

    def __init__(self, observable, unit_string: str | None, convert=None):
        if not isinstance(observable, Observable):
            raise ValueError(
                "ObservableUnit can only be assigned to Observable component."
            )
        unit_string = self._check_dimensionless(unit_string)
        self._unit_string = unit_string
        try:
            self._unit = u.Unit(unit_string)
            self._unit_string_parsed = self._unit.to_string()
        except:
            raise UnknownUnitError(
                "Unrecognizable unit pattern '{}'".format(unit_string)
            )
        if convert is not None:
            try:
                unit_orig = self._unit
                try:
                    unit_new = u.Unit(convert)
                except:
                    raise UnknownUnitError(
                        "Unrecognizable unit pattern '{}' for convert.".format(convert)
                    )
                self.conversion_factor = unit_orig.to(unit_new)
                self._unit = unit_new
                self._unit_string = convert
                self._unit_string_parsed = unit_new.to_string()
            except:
                raise UnitConversionError(
                    "Unable to convert units {} to {}".format(unit_string, convert)
                )
            is_conc_unit = unitdefs.is_concentration(self._unit)
            if not is_conc_unit:
                msg = "Observable {} must be assigned a concentration or amount unit pattern. Unit pattern {} isn't a recognized concentration or amount pattern.".format(
                    observable.name,
                    self._unit_string,
                )
                raise WrongUnitError(msg)
        self._obs = observable
        super(ParameterUnit, self).__init__(
            observable, self._unit_string, predicate="units"
        )
        self.name = "unit_" + observable.name
        observable.units = self
        observable.has_units = True
        return


class Unit(ExpressionUnit, ObservableUnit, ParameterUnit):
    """Unit object used to assign units to pysb model components.

    Unit can be assigned to Parameter, Expression, and Observable model components.
    However, end users should typically only apply units to Parameter components.

    Subclass of ExpressionUnit, ObservableUnit, and ParameterUnit.
    """

    def __init__(
        self,
        component: Parameter | Expression | Observable,
        unit_string: str | None,
        convert=None,
        obs_pattern=None,
    ):
        """_summary_

        Args:
            component (Parameter | Expression | Observable): The component to which units are being added.
            unit_string (str | None): The unit.
            convert (_type_, optional): Another unit to which we want to convert.
                Defaults to None. Ignored when SimulationUnits has been defined.
            obs_pattern (_type_, optional): Pattern of observables in an
                expression. Defaults to None.

        Raises:
            ValueError: If the input model component is unsupported.
        """

        if isinstance(component, Parameter):
            ParameterUnit.__init__(self, component, unit_string, convert=convert)
        elif isinstance(component, Expression):
            ExpressionUnit.__init__(
                self, component, unit_string, obs_pattern=obs_pattern
            )
        elif isinstance(component, Observable):
            ObservableUnit.__init__(self, component, unit_string, convert=convert)
        else:
            raise ValueError(
                "Unit can't be assigned to component type {}".format(
                    repr(type(component))
                )
            )
        return


# Utility functions:


def add_units(model_cls):
    @property
    def units(self):
        unit_list = []
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_list.append(annotation)
        return unit_list

    setattr(model_cls, "units", units)

    @property
    def unit_map(self):
        unit_dict = dict()
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_dict[annotation.subject.name] = annotation.object
        return unit_dict

    setattr(model_cls, "unit_map", unit_map)

    @property
    def reaction_order(self):
        orders = list()
        for rule in self.rules:
            order_forward = len(rule.reactant_pattern.complex_patterns)
            order_reverse = None
            if rule.is_reversible:
                order_reverse = len(rule.product_pattern.complex_patterns)

            orders.append([rule, order_forward, order_reverse])
        return orders

    setattr(model_cls, "reaction_order", reaction_order)

    return model_cls


def add_macro_units(macro_module):
    """Monkey patches a module by reassigning model components to be their units versions.

    Args:
        macro_module (module): The module to which we want add units.
    """
    try:
        macro_module.Rule = Rule
    except:
        pass
    try:
        macro_module.Parameter = Parameter
    except:
        pass
    try:
        macro_module.Expression = Expression
    except:
        pass
    try:
        macro_module.Observable = Observable
    except:
        pass
    try:
        macro_module.Initial = Initial
    except:
        pass
    return


def unitize(depth: int = 1) -> None:
    """Monkey patches the model definition modules namespace and replaces model components with their units versions.

    Args:
        depth (int, optional): The number of frames back to get to the model namespace. Defaults to 1.
            Maximum supported depth is 3.
    """
    import inspect

    frame = inspect.currentframe()
    if depth > 3:
        depth = 3
    if depth == 2:
        model_module_vars = frame.f_back.f_back.f_locals
    elif depth == 3:
        model_module_vars = frame.f_back.f_back.f_back.f_locals
    else:
        model_module_vars = frame.f_back.f_locals
    units_vars = globals()
    components_replace = [
        "Rule",
        "Parameter",
        "Expression",
        "Model",
        "Observable",
        "Initial",
    ]
    for component in components_replace:
        if component in model_module_vars:
            model_module_vars[component] = units_vars[component]

    if "Unit" not in model_module_vars:
        model_module_vars["Unit"] = Unit
    if "SimulationUnits" not in model_module_vars:
        model_module_vars["SimulationUnits"] = SimulationUnits
    if "set_molecule_volume" not in model_module_vars:
        model_module_vars["set_molecule_volume"] = set_molecule_volume
    return


def check(model: Model = None) -> None:
    """Check for duplicate, inconsistent, and missing units.

    Args:
        model (optional): The model to check. Defaults to None.
         If None, PySB's SelfExporter is used to set the current model
         in the calling namespace.
    """
    if model is None:
        model = SelfExporter.default_model
    try:
        units = model.units
    except:
        warnings.warn(
            "Model {} has no units to check.".format(model.name),
            UnitsWarning,
            stacklevel=3,
        )
        return

    # Here we check for any unit duplication where a component is assigned
    # multiple units.
    n_units = len(units)
    for i in range(n_units - 1):
        unit_i = units[i]
        subject_i = unit_i.subject
        for j in range(i + 1, n_units):
            unit_j = units[j]
            subject_j = unit_j.subject
            if subject_i == subject_j:

                warnings.warn(
                    "{} '{}' has been assigned multiple units.".format(
                        repr(type(subject_i))
                        .split(".")[-1]
                        .replace("'", "")
                        .replace(">", ""),
                        subject_i.name,
                    ),
                    UnitsWarning,
                    stacklevel=3,
                )

    # Here we compile the different unit types based on physical type
    # and cross-check for consistency amongst common physical type.
    unit_types = dict()
    for unit in units:
        if unitdefs.is_concentration(unit.unit):
            phys_type = "concentration"
        elif unitdefs.is_zero_order_rate_constant(unit.unit):
            phys_type = "reaction rate"
        elif unitdefs.is_second_order_rate_constant(unit.unit):
            phys_type = "second order rate constant"
        else:
            phys_type = unit.physical_type
        if phys_type not in unit_types.keys():
            unit_types[phys_type] = list()

        unit_types[phys_type].append(unit)

    for key in unit_types.keys():
        unis = unit_types[key]
        n_unis = len(unis)
        for i in range(n_unis - 1):
            uni_i = unis[i]
            type_i = (
                repr(type(uni_i.subject))
                .split(".")[-1]
                .replace("'", "")
                .replace(">", "")
            )
            sub_name_i = uni_i.subject.name
            uni_i_str = uni_i.value
            for j in range(i + 1, n_unis):
                uni_j = unis[j]
                type_j = (
                    repr(type(uni_j.subject))
                    .split(".")[-1]
                    .replace("'", "")
                    .replace(">", "")
                )
                sub_name_j = uni_j.subject.name
                uni_j_str = uni_j.value
                if not (uni_i.unit == uni_j.unit):

                    warnings.warn(
                        "Units '{}' for {} '{}' and '{}' for {} '{}' of unit-type '{}' do not match. \n Double-check units for consistency.".format(
                            uni_i_str,
                            type_i,
                            sub_name_i,
                            uni_j_str,
                            type_j,
                            sub_name_j,
                            key,
                        ),
                        UnitsWarning,
                        stacklevel=3,
                    )

    # Here we check for any parameters that don't have units.
    for param in model.parameters:
        if not param.has_units:
            warnings.warn(
                "Parameter '{}' hasn't been assigned any units.".format(param.name),
                UnitsWarning,
                stacklevel=3,
            )

    return


def rule_orders():

    for rule in SelfExporter.default_model.rules:
        complex_pattern = rule.reactant_pattern
        print(rule, rule.reactant_)
    return


def set_molecule_volume(value: float, unit: str) -> None:
    unitdefs.set_molecule_volume(value, unit)
    return


# Error Classes


class UnknownUnitError(ValueError):
    """An unrecognized unit type was added to the model."""

    pass


class MissingUnitError(ValueError):
    """A component is missing a needed unit."""

    pass


class WrongUnitError(ValueError):
    """A component has the wrong units for its intended usage."""

    pass


class DuplicateUnitError(ValueError):
    """A component already has units."""

    pass


class UnitConversionError(ValueError):
    """Unable to convert between two different units."""

    pass


# Warning Classes


class UnitsWarning(UserWarning):
    """There is a potential issue with the units."""

    pass
