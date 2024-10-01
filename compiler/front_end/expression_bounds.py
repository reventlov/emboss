# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functions for proving mathematical properties of expressions."""

import operator

from compiler.util import ir_num
from compiler.util import ir_data
from compiler.util import ir_data_utils
from compiler.util import ir_util
from compiler.util import traverse_ir


def compute_constraints_of_expression(expression, ir):
    """Adds appropriate bounding constraints to the given expression."""
    if ir_util.is_constant_type(expression.type):
        return
    expression_variety = expression.WhichOneof("expression")
    if expression_variety == "constant":
        _compute_constant_value_of_constant(expression)
    elif expression_variety == "constant_reference":
        _compute_constant_value_of_constant_reference(expression, ir)
    elif expression_variety == "function":
        _compute_constraints_of_function(expression, ir)
    elif expression_variety == "field_reference":
        _compute_constraints_of_field_reference(expression, ir)
    elif expression_variety == "builtin_reference":
        _compute_constraints_of_builtin_value(expression)
    elif expression_variety == "boolean_constant":
        _compute_constant_value_of_boolean_constant(expression)
    else:
        assert False, "Unknown expression variety {!r}".format(expression_variety)
    if expression.type.WhichOneof("type") == "integer":
        _assert_integer_constraints(expression)


def _compute_constant_value_of_constant(expression):
    value = expression.constant.value
    expression.type.integer.modular_value = value
    expression.type.integer.minimum_value = value
    expression.type.integer.maximum_value = value
    expression.type.integer.modulus = ir_num.INFINITY


def _compute_constant_value_of_constant_reference(expression, ir):
    referred_object = ir_util.find_object(
        expression.constant_reference.canonical_name, ir
    )
    expression = ir_data_utils.builder(expression)
    if isinstance(referred_object, ir_data.EnumValue):
        compute_constraints_of_expression(referred_object.value, ir)
        assert ir_util.is_constant(referred_object.value)
        new_value = ir_util.constant_value(referred_object.value)
        expression.type.enumeration.value = new_value
    elif isinstance(referred_object, ir_data.Field):
        assert ir_util.field_is_virtual(referred_object), (
            "Non-virtual non-enum-value constant reference should have been caught "
            "in type_check.py"
        )
        compute_constraints_of_expression(referred_object.read_transform, ir)
        expression.type.CopyFrom(referred_object.read_transform.type)
    else:
        assert False, "Unexpected constant reference type."


def _compute_constraints_of_function(expression, ir):
    """Computes the known constraints of the result of a function."""
    for arg in expression.function.args:
        compute_constraints_of_expression(arg, ir)
    op = expression.function.function
    if op in (ir_data.FunctionMapping.ADDITION, ir_data.FunctionMapping.SUBTRACTION):
        _compute_constraints_of_additive_operator(expression)
    elif op == ir_data.FunctionMapping.MULTIPLICATION:
        _compute_constraints_of_multiplicative_operator(expression)
    elif op in (
        ir_data.FunctionMapping.EQUALITY,
        ir_data.FunctionMapping.INEQUALITY,
        ir_data.FunctionMapping.LESS,
        ir_data.FunctionMapping.LESS_OR_EQUAL,
        ir_data.FunctionMapping.GREATER,
        ir_data.FunctionMapping.GREATER_OR_EQUAL,
        ir_data.FunctionMapping.AND,
        ir_data.FunctionMapping.OR,
    ):
        _compute_constant_value_of_comparison_operator(expression)
    elif op == ir_data.FunctionMapping.CHOICE:
        _compute_constraints_of_choice_operator(expression)
    elif op == ir_data.FunctionMapping.MAXIMUM:
        _compute_constraints_of_maximum_function(expression)
    elif op == ir_data.FunctionMapping.PRESENCE:
        _compute_constraints_of_existence_function(expression, ir)
    elif op in (
        ir_data.FunctionMapping.UPPER_BOUND,
        ir_data.FunctionMapping.LOWER_BOUND,
    ):
        _compute_constraints_of_bound_function(expression)
    else:
        assert False, "Unknown operator {!r}".format(op)


def _compute_constraints_of_existence_function(expression, ir):
    """Computes the constraints of a $has(field) expression."""
    field_path = expression.function.args[0].field_reference.path[-1]
    field = ir_util.find_object(field_path, ir)
    compute_constraints_of_expression(field.existence_condition, ir)
    ir_data_utils.builder(expression).type.CopyFrom(field.existence_condition.type)


def _compute_constraints_of_field_reference(expression, ir):
    """Computes the constraints of a reference to a structure's field."""
    field_path = expression.field_reference.path[-1]
    field = ir_util.find_object(field_path, ir)
    if isinstance(field, ir_data.Field) and ir_util.field_is_virtual(field):
        # References to virtual fields should have the virtual field's constraints
        # copied over.
        compute_constraints_of_expression(field.read_transform, ir)
        ir_data_utils.builder(expression).type.CopyFrom(field.read_transform.type)
        return
    # Non-virtual non-integer fields do not (yet) have constraints.
    if expression.type.WhichOneof("type") == "integer":
        # TODO(bolms): These lines will need to change when support is added for
        # fixed-point types.
        expression.type.integer.modulus = ir_num.Num(1)
        expression.type.integer.modular_value = ir_num.Num(0)
        type_definition = ir_util.find_parent_object(field_path, ir)
        if isinstance(field, ir_data.Field):
            referrent_type = field.type
        else:
            referrent_type = field.physical_type_alias
        if referrent_type.HasField("size_in_bits"):
            type_size = ir_util.constant_value(referrent_type.size_in_bits)
        else:
            field_size = ir_util.constant_value(field.location.size)
            if field_size is None:
                type_size = None
            else:
                type_size = field_size * type_definition.addressable_unit
        assert referrent_type.HasField("atomic_type"), field
        assert not referrent_type.atomic_type.reference.canonical_name.module_file
        _set_integer_constraints_from_physical_type(
            expression, referrent_type, type_size
        )


def _set_integer_constraints_from_physical_type(expression, physical_type, type_size):
    """Copies the integer constraints of an expression from a physical type."""
    # SCAFFOLDING HACK: In order to keep changelists manageable, this hardcodes
    # the ranges for all of the Emboss Prelude integer types.   This would break
    # any user-defined `external` integer types, but that feature isn't fully
    # implemented in the C++ backend, so it doesn't matter for now.
    #
    # Adding the attribute(s) for integer bounds will require new operators:
    # integer/flooring division, remainder, and exponentiation (2**N, 10**N).
    #
    # (Technically, there are a few sets of operators that would work: for
    # example, just the choice operator `?:` is sufficient, but very ugly.
    # Bitwise AND, bitshift, and exponentiation would also work, but `10**($bits
    # >> 2) * 2**($bits & 0b11) - 1` isn't quite as clear as `10**($bits // 4) *
    # 2**($bits % 4) - 1`, in my (bolms@) opinion.)
    #
    # TODO(bolms): Add a scheme for defining integer bounds on user-defined
    # external types.
    if type_size is None:
        # If the type_size is unknown, then we can't actually say anything about the
        # minimum and maximum values of the type.  For UInt, Int, and Bcd, an error
        # will be thrown during the constraints check stage.
        expression.type.integer.minimum_value = ir_num.NEGATIVE_INFINITY
        expression.type.integer.maximum_value = ir_num.INFINITY
        return
    name = tuple(physical_type.atomic_type.reference.canonical_name.object_path)
    if name == ("UInt",):
        expression.type.integer.minimum_value = ir_num.Num(0)
        expression.type.integer.maximum_value = ir_num.Num(2**type_size - 1)
    elif name == ("Int",):
        expression.type.integer.minimum_value = ir_num.Num(-(2 ** (type_size - 1)))
        expression.type.integer.maximum_value = ir_num.Num(2 ** (type_size - 1) - 1)
    elif name == ("Bcd",):
        expression.type.integer.minimum_value = ir_num.Num(0)
        expression.type.integer.maximum_value = ir_num.Num(
            10 ** (type_size // 4) * 2 ** (type_size % 4) - 1
        )
    else:
        assert False, "Unknown integral type " + ".".join(name)


def _compute_constraints_of_parameter(parameter):
    if parameter.type.WhichOneof("type") == "integer":
        type_size = ir_util.constant_value(parameter.physical_type_alias.size_in_bits)
        _set_integer_constraints_from_physical_type(
            parameter, parameter.physical_type_alias, type_size
        )


def _compute_constraints_of_builtin_value(expression):
    """Computes the constraints of a builtin (like $static_size_in_bits)."""
    name = expression.builtin_reference.canonical_name.object_path[0]
    if name == "$static_size_in_bits":
        expression.type.integer.modulus = ir_num.Num(1)
        expression.type.integer.modular_value = ir_num.Num(0)
        expression.type.integer.minimum_value = ir_num.Num(0)
        # The maximum theoretically-supported size of something is 2**64 bytes,
        # which is 2**64 * 8 bits.
        #
        # Really, $static_size_in_bits is only valid in expressions that have to be
        # evaluated at compile time anyway, so it doesn't really matter if the
        # bounds are excessive.
        expression.type.integer.maximum_value = ir_num.INFINITY
    elif name == "$is_statically_sized":
        # No bounds on a boolean variable.
        pass
    elif name == "$logical_value":
        # $logical_value is the placeholder used in inferred write-through
        # transformations.
        #
        # Only integers (currently) have "real" write-through transformations, but
        # fields that would otherwise be straight aliases, but which have a
        # [requires] attribute, are elevated to write-through fields, so that the
        # [requires] clause can be checked in Write, CouldWriteValue, TryToWrite,
        # Read, and Ok.
        if expression.type.WhichOneof("type") == "integer":
            assert expression.type.integer.modulus is not None
            assert expression.type.integer.modular_value is not None
            assert expression.type.integer.minimum_value is not None
            assert expression.type.integer.maximum_value is not None
        elif expression.type.WhichOneof("type") == "enumeration":
            assert expression.type.enumeration.name
        elif expression.type.WhichOneof("type") == "boolean":
            pass
        else:
            assert False, "Unexpected type for $logical_value"
    else:
        assert False, "Unknown builtin " + name


def _compute_constant_value_of_boolean_constant(expression):
    expression.type.boolean.value = expression.boolean_constant.value


def _compute_constraints_of_additive_operator(expression):
    """Computes the modular value of an additive expression."""
    funcs = {
        ir_data.FunctionMapping.ADDITION: lambda x, y: x + y,
        ir_data.FunctionMapping.SUBTRACTION: lambda x, y: x - y,
    }
    func = funcs[expression.function.function]
    args = expression.function.args
    for arg in args:
        assert arg.type.integer.modular_value is not None, str(expression)
    left, right = args
    unadjusted_modular_value = func(
        left.type.integer.modular_value, right.type.integer.modular_value
    )
    new_modulus = ir_num.gcd(left.type.integer.modulus, right.type.integer.modulus)
    expression.type.integer.modulus = new_modulus
    expression.type.integer.modular_value = unadjusted_modular_value % new_modulus
    lmax = left.type.integer.maximum_value
    lmin = left.type.integer.minimum_value
    if expression.function.function == ir_data.FunctionMapping.SUBTRACTION:
        rmax = right.type.integer.minimum_value
        rmin = right.type.integer.maximum_value
    else:
        rmax = right.type.integer.maximum_value
        rmin = right.type.integer.minimum_value
    expression.type.integer.minimum_value = func(lmin, rmin)
    expression.type.integer.maximum_value = func(lmax, rmax)


def _compute_constraints_of_multiplicative_operator(expression):
    """Computes the modular value of a multiplicative expression."""
    bounds = [arg.type.integer for arg in expression.function.args]

    # The minimum and maximum values can come from any of the four pairings of
    # (left min, left max) with (right min, right max), depending on the signs and
    # magnitudes of the minima and maxima.  E.g.:
    #
    # max = left max * right max: [ 2,  3] * [ 2,  3]
    # max = left min * right min: [-3, -2] * [-3, -2]
    # max = left max * right min: [-3, -2] * [ 2,  3]
    # max = left min * right max: [ 2,  3] * [-3, -2]
    # max = left max * right max: [-2,  3] * [-2,  3]
    # max = left min * right min: [-3,  2] * [-3,  2]
    #
    # For uncorrelated multiplication, the minimum and maximum will always come
    # from multiplying one extreme by another: if x is nonzero, then
    #
    #     (y + e) * x > y * x  ||  (y - e) * x > y * x
    #
    # for arbitrary nonzero e, so the extrema can only occur when we either cannot
    # add or cannot subtract e.
    #
    # Correlated multiplication (e.g., `x * x`) can have tighter bounds, but
    # Emboss is not currently trying to be that smart.
    lmin, lmax = bounds[0].minimum_value, bounds[0].maximum_value
    rmin, rmax = bounds[1].minimum_value, bounds[1].maximum_value
    extrema = [lmax * rmax, lmin * rmax, lmax * rmin, lmin * rmin]
    minimum_value = min(extrema)
    maximum_value = max(extrema)
    expression.type.integer.minimum_value = minimum_value
    expression.type.integer.maximum_value = maximum_value
    if minimum_value == maximum_value:
        expression.type.integer.modular_value = minimum_value
        expression.type.integer.modulus = ir_num.INFINITY
        return

    if all(bound.modulus.is_infinite() for bound in bounds):
        # If both sides are constant, the result is constant.
        expression.type.integer.modulus = ir_num.INFINITY
        expression.type.integer.modular_value = (
            bounds[0].modular_value * bounds[1].modular_value
        )
        return

    if any(bound.modulus.is_infinite() for bound in bounds):
        # If one side is constant and the other is not, then the non-constant
        # modulus and modular_value can both be multiplied by the constant.
        # E.g., if `a` is congruent to 3 mod 5, then `4 * a` will be congruent
        # to 12 mod 20:
        #
        #   a = ...   |  4 * a = ...  |  4 * a mod 20 = ...
        #   3         |  12           |  12
        #   8         |  32           |  12
        #   13        |  52           |  12
        #   18        |  72           |  12
        #   23        |  92           |  12
        #   28        |  112          |  12
        #   33        |  132          |  12
        #
        # This is trivially shown by noting that the difference between
        # consecutive possible values for `4 * a` always differ by 20.
        if bounds[0].modulus == ir_num.INFINITY:
            constant, variable = bounds
        else:
            variable, constant = bounds
        new_modulus = variable.modulus * abs(constant.modular_value)
        expression.type.integer.modulus = new_modulus
        # The `% new_modulus` will force the `modular_value` to be positive,
        # even when `constant.modular_value` is negative.
        expression.type.integer.modular_value = (
            variable.modular_value * constant.modular_value % new_modulus
        )
        return

    # If neither side is constant, then the result is more complex.  Full proof
    # is available in g3doc/modular_congruence_multiplication_proof.md
    #
    # Essentially, if:
    #
    # l == _ * l_mod + l_mv
    # r == _ * r_mod + r_mv
    #
    # Then we find l_mod0 and r_mod0 in:
    #
    # l == (_ * l_mod_nz + l_mv_nz) * l_mod0
    # r == (_ * r_mod_nz + r_mv_nz) * r_mod0
    #
    # And finally conclude:
    #
    # l * r == _ * GCD(l_mod_nz, r_mod_nz) * l_mod0 * r_mod0 + l_mv * r_mv
    product_of_zero_congruence_moduli = 1
    product_of_modular_values = 1
    nonzero_congruence_moduli = []
    for bound in bounds:
        zero_congruence_modulus = ir_num.gcd(bound.modulus, bound.modular_value)
        assert bound.modulus % zero_congruence_modulus == 0
        product_of_zero_congruence_moduli *= zero_congruence_modulus
        product_of_modular_values *= bound.modular_value
        nonzero_congruence_moduli.append(bound.modulus // zero_congruence_modulus)
    shared_nonzero_congruence_modulus = ir_num.gcd(
        nonzero_congruence_moduli[0], nonzero_congruence_moduli[1]
    )
    final_modulus = (
        shared_nonzero_congruence_modulus * product_of_zero_congruence_moduli
    )
    expression.type.integer.modulus = final_modulus
    expression.type.integer.modular_value = product_of_modular_values % final_modulus


def _assert_integer_constraints(expression):
    """Asserts that the integer bounds of expression are self-consistent.

    Asserts that `minimum_value` and `maximum_value` are congruent to
    `modular_value` modulo `modulus`.

    If `modulus` is "infinity", asserts that `minimum_value`, `maximum_value`, and
    `modular_value` are all equal.

    If `minimum_value` is equal to `maximum_value`, asserts that `modular_value`
    is equal to both, and that `modulus` is "infinity".

    Arguments:
        expression: an expression with type.integer

    Returns:
        None
    """
    bounds = expression.type.integer
    if bounds.modulus == ir_num.INFINITY:
        assert bounds.minimum_value == bounds.modular_value, f"{bounds}"
        assert bounds.maximum_value == bounds.modular_value, f"{bounds}"
        return
    modulus = bounds.modulus
    assert modulus > 0
    if bounds.minimum_value != ir_num.NEGATIVE_INFINITY:
        assert bounds.minimum_value % modulus == bounds.modular_value
    if bounds.maximum_value != ir_num.INFINITY:
        assert bounds.maximum_value % modulus == bounds.modular_value
    if bounds.minimum_value == bounds.maximum_value:
        # TODO(bolms): I believe there are situations using the
        # not-yet-implemented integer division operator that would trigger
        # these asserts, so they should be turned into assignments (with
        # corresponding tests) when implementing division.
        assert bounds.modular_value == bounds.minimum_value
        assert bounds.modulus == ir_num.INFINITY
    assert (
        bounds.minimum_value <= bounds.maximum_value
    ), f"{bounds.minimum_value} > {bounds.maximum_value}"


def _compute_constant_value_of_comparison_operator(expression):
    """Computes the constant value, if any, of a comparison operator."""
    args = expression.function.args
    if all(ir_util.is_constant(arg) for arg in args):
        functions = {
            ir_data.FunctionMapping.EQUALITY: operator.eq,
            ir_data.FunctionMapping.INEQUALITY: operator.ne,
            ir_data.FunctionMapping.LESS: operator.lt,
            ir_data.FunctionMapping.LESS_OR_EQUAL: operator.le,
            ir_data.FunctionMapping.GREATER: operator.gt,
            ir_data.FunctionMapping.GREATER_OR_EQUAL: operator.ge,
            ir_data.FunctionMapping.AND: operator.and_,
            ir_data.FunctionMapping.OR: operator.or_,
        }
        func = functions[expression.function.function]
        expression.type.boolean.value = func(
            *[ir_util.constant_value(arg) for arg in args]
        )


def _compute_constraints_of_bound_function(expression):
    """Computes the constraints of $upper_bound or $lower_bound."""
    if expression.function.function == ir_data.FunctionMapping.UPPER_BOUND:
        value = expression.function.args[0].type.integer.maximum_value
    elif expression.function.function == ir_data.FunctionMapping.LOWER_BOUND:
        value = expression.function.args[0].type.integer.minimum_value
    else:
        assert False, "Non-bound function"
    expression.type.integer.minimum_value = value
    expression.type.integer.maximum_value = value
    expression.type.integer.modular_value = value
    expression.type.integer.modulus = ir_num.INFINITY


def _compute_constraints_of_maximum_function(expression):
    """Computes the constraints of the $max function."""
    assert expression.type.WhichOneof("type") == "integer"
    args = expression.function.args
    assert args[0].type.WhichOneof("type") == "integer"
    # The minimum value of the result occurs when every argument takes its minimum
    # value, which means that the minimum result is the maximum-of-minimums.
    expression.type.integer.minimum_value = max(
        [arg.type.integer.minimum_value for arg in args]
    )
    # The maximum result is the maximum-of-maximums.
    expression.type.integer.maximum_value = max(
        [arg.type.integer.maximum_value for arg in args]
    )
    # If the expression is dominated by a constant factor, then the result is
    # constant.
    if expression.type.integer.minimum_value == expression.type.integer.maximum_value:
        expression.type.integer.modular_value = expression.type.integer.minimum_value
        expression.type.integer.modulus = ir_num.INFINITY
        return
    result_modulus = args[0].type.integer.modulus
    result_modular_value = args[0].type.integer.modular_value
    # The result of $max(a, b) could be either a or b, which means that the result
    # of $max(a, b) uses the _shared_modular_value() of a and b, just like the
    # choice operator '?:'.
    #
    # This also takes advantage of the fact that $max(a, b, c, d, ...) is
    # equivalent to $max(a, $max(b, $max(c, $max(d, ...)))), so it is valid to
    # call _shared_modular_value() in a loop.
    for arg in args[1:]:
        # TODO(bolms): I think the bounds could be tighter in some cases where
        # arg.maximum_value is less than the new expression.minimum_value, and
        # in some very specific cases where arg.maximum_value is greater than the
        # new expression.minimum_value, but arg.maximum_value - arg.modulus is less
        # than expression.minimum_value.
        result_modulus, result_modular_value = _shared_modular_value(
            (result_modulus, result_modular_value),
            (arg.type.integer.modulus, arg.type.integer.modular_value),
        )
    expression.type.integer.modulus = result_modulus
    expression.type.integer.modular_value = result_modular_value


def _shared_modular_value(left, right):
    """Returns the shared modulus and modular value of left and right.

    Arguments:
      left: A tuple of (modulus, modular value)
      right: A tuple of (modulus, modular value)

    Returns:
      A tuple of (modulus, modular_value) such that:

      left.modulus % result.modulus == 0
      right.modulus % result.modulus == 0
      left.modular_value % result.modulus = result.modular_value
      right.modular_value % result.modulus = result.modular_value

      That is, the result.modulus and result.modular_value will be compatible
      with, but (possibly) less restrictive than both left.(modulus,
      modular_value) and right.(modulus, modular_value).
    """
    left_modulus, left_modular_value = left
    right_modulus, right_modular_value = right
    # The combined modulus is gcd(gcd(left_modulus, right_modulus),
    # left_modular_value - right_modular_value).
    #
    # The inner gcd normalizes the left_modulus and right_modulus, but can leave
    # incompatible modular_values.  The outer gcd finds a modulus to which both
    # modular_values are congruent.  Some examples:
    #
    #     left          |  right         |  result
    #     --------------+----------------+--------------------
    #     l % 12 == 7   |  r % 20 == 15  |  res % 4 == 3
    #     l == 35       |  r % 20 == 15  |  res % 20 == 15
    #     l % 24 == 15  |  r % 12 == 7   |  res % 4 == 3
    #     l % 20 == 15  |  r % 20 == 10  |  res % 5 == 0
    #     l % 20 == 16  |  r % 20 == 11  |  res % 5 == 1
    #     l == 10       |  r == 7        |  res % 3 == 1
    #     l == 4        |  r == 4        |  res == 4
    #
    # The cases where one side or the other are constant are handled
    # automatically by the fact that ir_num.gcd("infinity", x) is x.
    common_modulus = ir_num.gcd(left_modulus, right_modulus)
    new_modulus = ir_num.gcd(
        common_modulus, abs(left_modular_value - right_modular_value)
    )
    if new_modulus == ir_num.INFINITY:
        # The only way for the new_modulus to come out as "infinity" *should* be
        # if both if_true and if_false have the same constant value.
        assert left_modular_value == right_modular_value
        assert left_modulus == right_modulus == ir_num.INFINITY
        return new_modulus, left_modular_value
    else:
        assert left_modular_value % new_modulus == right_modular_value % new_modulus
        return new_modulus, left_modular_value % new_modulus


def _compute_constraints_of_choice_operator(expression):
    """Computes the constraints of a choice operation '?:'."""
    condition, if_true, if_false = ir_data_utils.reader(expression).function.args
    expression = ir_data_utils.builder(expression)
    if condition.type.boolean.HasField("value"):
        # The generated expressions for $size_in_bits and $size_in_bytes look like
        #
        #     $max((field1_existence_condition ? field1_start + field1_size : 0),
        #          (field2_existence_condition ? field2_start + field2_size : 0),
        #          (field3_existence_condition ? field3_start + field3_size : 0),
        #          ...)
        #
        # Since most existence_conditions are just "true", it is important to select
        # the tighter bounds in those cases -- otherwise, only zero-length
        # structures could have a constant $size_in_bits or $size_in_bytes.
        side = if_true if condition.type.boolean.value else if_false
        expression.type.CopyFrom(side.type)
        return
    # The type.integer minimum_value/maximum_value bounding code is needed since
    # constraints.check_constraints() will complain if minimum and maximum are not
    # set correctly.  I'm (bolms@) not sure if the modulus/modular_value pulls its
    # weight, but for completeness I've left it in.
    if if_true.type.WhichOneof("type") == "integer":
        # The minimum value of the choice is the minimum value of either side, and
        # the maximum is the maximum value of either side.
        expression.type.integer.minimum_value = min(
            if_true.type.integer.minimum_value,
            if_false.type.integer.minimum_value,
        )
        expression.type.integer.maximum_value = max(
            if_true.type.integer.maximum_value,
            if_false.type.integer.maximum_value,
        )
        new_modulus, new_modular_value = _shared_modular_value(
            (if_true.type.integer.modulus, if_true.type.integer.modular_value),
            (if_false.type.integer.modulus, if_false.type.integer.modular_value),
        )
        expression.type.integer.modulus = new_modulus
        expression.type.integer.modular_value = new_modular_value
    else:
        assert if_true.type.WhichOneof("type") in (
            "boolean",
            "enumeration",
        ), "Unknown type {} for expression".format(if_true.type.WhichOneof("type"))


def compute_constants(ir):
    """Computes constant values for all expressions in ir.

    compute_constants calculates all constant values and adds them to the type
    information for each expression and subexpression.

    Arguments:
        ir: an IR on which to compute constants

    Returns:
        A (possibly empty) list of errors.
    """
    traverse_ir.fast_traverse_ir_top_down(
        ir,
        [ir_data.Expression],
        compute_constraints_of_expression,
        skip_descendants_of={ir_data.Expression},
    )
    traverse_ir.fast_traverse_ir_top_down(
        ir,
        [ir_data.RuntimeParameter],
        _compute_constraints_of_parameter,
        skip_descendants_of={ir_data.Expression},
    )
    return []
