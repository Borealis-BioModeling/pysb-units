from pysb.core import SelfExporter
import pysb
import astropy.units as u

## New Units class ##


class Units(pysb.Annotation):

    def __init__(self, parameter, unit_string):
        self._unit_string = unit_string
        self._unit = unit_string
        self._param = parameter
        super().__init__(parameter, self._unit, predicate="units")
        parameter.units = self
        parameter.has_units = True
        return

    # def _parse(self, unit_string):
    #     # replace any ^-1 with 1 / 
    #     # unit_string = unit_string.replace("^", "**")
    #     try:
    #         unit = u.Unit(unit_string)
    #     except UnknownUnitError as e:
    #         raise e 
    #     parsed = unit.to_string()

    @property
    def value(self):
        return self._unit_string

    def __repr__(self):
        repr_string = super().__repr__()
        split = repr_string.split(",")
        return "%s, %s)" % (split[0], split[1])


## Drop-ins for model components with added units features. ##


class Model(pysb.Model):

    @property
    def units(self):
        unit_list = []
        for annotation in self.annotations:
            if isinstance(annotation, Units):
                unit_list.append(annotation)
        return unit_list

    @property
    def unit_map(self):
        unit_dict = dict()
        for annotation in self.annotations:
            if isinstance(annotation, Units):
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
            return "%s(%s, %s), unit=%s" % (
                self.__class__.__name__,
                repr(self.name),
                repr(self.value),
                repr(self.units.value),
            )
        else:
            return super().__repr__()


class Initial(pysb.Initial):

    def __init__(self, pattern, value, fixed=False, _export=True):
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
            ret += ", unit=" + self.units.value
        return ret


# Utility functions:


def add_units(model_cls):
    @property
    def units(self):
        unit_list = []
        for annotation in self.annotations:
            if isinstance(annotation, Units):
                unit_list.append(annotation)
        return unit_list

    setattr(model_cls, "units", units)

    @property
    def unit_map(self):
        unit_dict = dict()
        for annotation in self.annotations:
            if isinstance(annotation, Units):
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
