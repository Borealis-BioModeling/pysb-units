import sympy
from pysb.core import SelfExporter
import pysb
import astropy.units as u
from abc import ABC
from pysb.units import unitdefs

# Define __all__

__all__ = [
    "Unit",
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
]

# Enable the custom units if not already enabled.
try:
    unitdefs.enable()
except:
    pass

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


class ParameterUnit(pysb.Annotation):


    def __init__(self, parameter, unit_string, convert=None):
        if not isinstance(parameter, Parameter):
            raise ValueError(
                "ParameterUnit can only be assigned to Parameter component."
            )
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
                conversion_factor = unit_orig.to(unit_new)
                parameter.value *= conversion_factor
                self._unit = unit_new
                self._unit_string = convert
                self._unit_string_parsed = unit_new.to_string()
            except:
                raise ValueError(
                    "Unable to convert units {} to {}".format(unit_string, convert)
                )
        self._param = parameter
        super().__init__(parameter, self._unit_string, predicate="units")
        self.name = "unit_" + parameter.name
        parameter.units = self
        parameter.has_units = True
        return

    @property
    def value(self):
        return self._unit_string

    @property
    def unit(self):
        return self._unit

    def __repr__(self):
        repr_string = super().__repr__()
        split = repr_string.split(",")
        return "%s, %s)" % (split[0], split[1])

    @property
    def expr(self):
        unit_bases = self.unit.bases
        unit_powers = self.unit.powers
        unit_symbols = [sympy.Symbol(base.to_string()) for base in unit_bases]
        return sympy.Mul(*[a**b for a, b in zip(unit_symbols, unit_powers)])


class ExpressionUnit(ParameterUnit):

    def __init__(self, expression, unit_string, obs_pattern=None):
        if not isinstance(expression, Expression):
            raise ValueError(
                "ExpressionUnit can only be assigned to Expression component."
            )
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

    def __init__(self, observable, unit_string, convert=None):
        if not isinstance(observable, Observable):
            raise ValueError(
                "ObservableUnit can only be assigned to Observable component."
            )
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
                raise ValueError(
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

    def __init__(self, component, unit_string, convert=None, obs_pattern=None):
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


## Drop-ins for model components with added units features. ##


class Model(pysb.Model):

    @property
    def units(self):
        unit_list = []
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_list.append(annotation)
        return unit_list

    @property
    def unit_map(self):
        unit_dict = dict()
        for annotation in self.annotations:
            if isinstance(annotation, Unit):
                unit_dict[annotation.subject.name] = annotation.object
        return unit_dict

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


class Parameter(pysb.Parameter):

    def __init__(self, name, value=0.0, _export=True, nonnegative=True, integer=False):
        super().__init__(name, value, _export, nonnegative, integer)
        self.units = None
        self.has_units = False
        return

    def __repr__(self):
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
        return self.units.unit


class Expression(pysb.Expression):

    def __init__(self, name, expr, _export=True):
        unit_string, obs_pattern = self._compose_units(expr)
        # print(unit_string, obs_string)
        super().__init__(name, expr, _export=_export)
        self.units = None
        self.has_units = False
        expr_unit = Unit(self, unit_string, obs_pattern=obs_pattern)
        return

    def __repr__(self):
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
        """Return expr rewritten in terms of terminal symbols only."""
        subs = []
        subs_uni = []
        subs_obs = []
        for a in expr.atoms():
            if isinstance(a, Expression):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
            elif isinstance(a, Parameter):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
            elif isinstance(a, pysb.Observable):
                if a.has_units:
                    subs.append((a, a.units.expr))
                    subs_uni.append((a, 1))
                else:
                    subs_obs.append([a, 1])
        unit_obs_expr = expr.subs(subs)
        unit_expr = unit_obs_expr.subs(subs_obs)
        obs_expr = expr.subs(subs_uni)
        unit_string = repr(unit_expr)
        if len(subs_obs) > 0:
            if isinstance(obs_expr, Observable):
                obs_string = repr(obs_expr.name)
            else:
                obs_string = repr(obs_expr)
        else:
            obs_string = None
        return unit_string, obs_string


class Observable(pysb.Observable):

    def __init__(self, *args, **kwargs):
        self.units = None
        self.has_units = False
        super().__init__(*args, **kwargs)


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


def check_units():
    print(SelfExporter.default_model.units)


def rule_orders():

    for rule in SelfExporter.default_model.rules:
        complex_pattern = rule.reactant_pattern
        print(rule, rule.reactant_)
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
