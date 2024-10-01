# Copyright 2024 Google LLC
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

import dataclasses
import math

_INF = "infinity"
_NEG_INF = "-infinity"
_ERR = "error"


def _maybe_augment(value):
    if value in (_INF, _NEG_INF, _ERR) or isinstance(value, int):
        return Num(value)
    else:
        return value


class Num:
    _value: int | str

    def __init__(self, value=0):
        if value in (_INF, _NEG_INF, _ERR):
            self._value = value
        elif isinstance(value, int):
            self._value = value
        elif isinstance(value, Num):
            self._value = value.value
        else:
            self._value = int(value)
            # raise ValueError(f"Cannot construct Num from {repr(value)}")

    @property
    def value(self):
        return self._value

    def is_infinite(self):
        return self.value in (_INF, _NEG_INF)

    def is_error(self):
        return self.value == _ERR

    def is_integer(self):
        return isinstance(self.value, int)

    def sign(self):
        if self.is_error():
            raise ValueError("Cannot take sign of value 'error'.")
        elif self > 0:
            return 1
        elif self < 0:
            return -1
        else:
            return 0

    def __bool__(self):
        if self.is_error():
            raise ValueError("Cannot convert value 'error' to bool.")
        return bool(self.value)

    def __hash__(self):
        return hash(self.value)

    def __int__(self):
        if not self.is_integer():
            raise ValueError(f"Cannot convert {self.value} to int.")
        return self.value

    def __eq__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self.value == other.value

    def __ne__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self.value != other.value

    def __lt__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._lt(other)

    def _lt(self, other):
        if self.value == _ERR or other.value == _ERR:
            raise ArithmeticError("Cannot order value 'error'.")
        elif other.value == _NEG_INF:
            return False
        elif self.value == _INF:
            return False
        elif other.value == _INF:
            return self.value != _INF
        elif self.value == _NEG_INF:
            return other.value != _NEG_INF
        else:
            return self.value < other.value

    def __le__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._le(other)

    def _le(self, other):
        if self.value == _ERR or other.value == _ERR:
            raise ArithmeticError("Cannot order value 'error'.")
        elif other.value == _NEG_INF:
            return self.value == _NEG_INF
        elif self.value == _INF:
            return other.value == _INF
        elif other.value == _INF:
            return True
        elif self.value == _NEG_INF:
            return True
        else:
            return self.value <= other.value

    def __gt__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._gt(other)

    def _gt(self, other):
        if self.value == _ERR or other.value == _ERR:
            raise ArithmeticError("Cannot order value 'error'.")
        elif other.value == _NEG_INF:
            return self.value != _NEG_INF
        elif self.value == _INF:
            return other.value != _INF
        elif other.value == _INF:
            return False
        elif self.value == _NEG_INF:
            return False
        else:
            return self.value > other.value

    def __ge__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._ge(other)

    def _ge(self, other):
        if self.value == _ERR or other.value == _ERR:
            raise ArithmeticError("Cannot order value 'error'.")
        elif other.value == _NEG_INF:
            return True
        elif self.value == _INF:
            return True
        elif other.value == _INF:
            return self.value == _INF
        elif self.value == _NEG_INF:
            return other.value == _NEG_INF
        else:
            return self.value >= other.value

    def __neg__(self):
        if self.value == _ERR:
            return ERROR
        if self.value == _INF:
            return NEGATIVE_INFINITY
        if self.value == _NEG_INF:
            return INFINITY
        return Num(-self.value)

    def __pos__(self):
        if self.value == _ERR:
            return ERROR
        return self

    def __abs__(self):
        if self.value == _ERR:
            return ERROR
        elif self.__lt__(0):
            return self.__neg__()
        else:
            return self

    def __add__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._add(other)

    def __radd__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._add(self)

    def _add(self, other):
        if self.value == _ERR or other.value == _ERR:
            return ERROR
        if self.is_infinite():
            self, other = other, self
        if other.value == _INF:
            if self.value == _NEG_INF:
                return ERROR
            else:
                return INFINITY
        elif other.value == _NEG_INF:
            if self.value == _INF:
                return ERROR
            else:
                return NEGATIVE_INFINITY
        else:
            return Num(self.value + other.value)

    def __sub__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._add(other.__neg__())

    def __rsub__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._add(self.__neg__())

    def __mul__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._mul(other)

    def __rmul__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._mul(self)

    def _mul(self, other):
        if self.value == _ERR or other.value == _ERR:
            return ERROR
        if self.is_infinite() or other.is_infinite():
            sign = self.sign() * other.sign()
            if sign > 0:
                return INFINITY
            elif sign < 0:
                return NEGATIVE_INFINITY
            else:
                return Num(0)
        return Num(self.value * other.value)

    def __mod__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._mod(other)

    def __rmod__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._mod(self)

    def _mod(self, other):
        # This uses the definition of modulus that Python uses:
        #
        # 1.  x % y is always either 0 or between 0 and y
        # 2.  x % y is equal to adding or subtracting y to or from x until the first
        #     property is true
        #
        # "infinity", in Emboss, is a singular notional value that roughly
        # corresponds to the grade-school version of ∞.  It does NOT correspond
        # to ω+n or א+n for any n -- that is, the Emboss infinity is not an
        # infinite ordinal or infinite cardinal value.  Technically, it is just
        # an arbitrary value that has been added to the set of integers for the
        # purposes of Emboss arithmetic, and in Emboss it is mostly used as a
        # sentinel value to mean "no upper bound" or "the value is exact".
        # (Its twin, "-infinity", is used to mean "no lower bound".)
        #
        # Under the Emboss definition of "infinity", x % infinity should == x,
        # for any value x >= 0 and < infinity, because x is already between 0
        # and infinity.  infinity % infinity is "error", because subtracting
        # infinity from infinity yields "error".  For any x < 0, x % infinity
        # should have no true result -- x is not between 0 and infinity, so we
        # would need to add infinity to x, but that jumps past all finite
        # positive numbers and yields infinity, which is not strictly less than
        # infinity.  However, we define x % infinity to be simply x for all
        # finite values of x, which simplifies modular bounds computations.
        #
        # Similar logic holds for the result of x % -infinity, but for now, all such
        # computations are simply considered to be "error".
        #
        # This may need to be revisited for handling the modulus operator.
        if self.value == _ERR or other.value == _ERR:
            return ERROR
        if self.is_infinite():
            return ERROR
        elif other.value == _INF:
            return self
        elif other.value == _NEG_INF:
            return ERROR
        else:
            return Num(self.value % other.value)

    def __floordiv__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._floordiv(other)

    def __rfloordiv__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._floordiv(self)

    def _floordiv(self, other):
        if self.value == _ERR or other.value == _ERR:
            return ERROR
        if self.is_infinite():
            if other.is_infinite():
                return ERROR
            else:
                return self.__mul__(other.sign())
        else:
            if other.is_infinite():
                return Num(0)
            else:
                return Num(self.value // other.value)

    def __pow__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return self._pow(other)

    def __rpow__(self, other):
        other = _maybe_augment(other)
        if not isinstance(other, Num):
            return NotImplemented
        return other._pow(self)

    def _pow(self, other):
        if self.value == _ERR or other.value == _ERR:
            return ERROR
        if other._lt(Num(0)):
            return ERROR
        elif other.value == 0:
            if self.value == 0:
                # This is arguably just 1, but better start safe.
                return ERROR
            else:
                return Num(1)
        elif other.value == _INF:
            if self._lt(Num(0)):
                return ERROR
            elif self.value in (0, 1):
                return self
            else:
                return INFINITY
        else:
            if self.value == _NEG_INF:
                if other.value % 2 == 0:
                    return INFINITY
                else:
                    return NEGATIVE_INFINITY
            elif self.value == _INF:
                return INFINITY
            else:
                return Num(self.value**other.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"Num({self.value})"


def gcd(a, b):
    """Returns the greatest common divisor (GCD) of a and b.

    Arguments:
        a: a Num or something convertible to Num
        b: a Num or something convertible to Num

    Returns:
        The largest Num that evenly divides both `a` and `b`.

        "infinity" is divisible by all integers.  If `a` is infinite, the
        result is `abs(b)`, and vice versa.  It also means that if `a == b ==
        0`, the GCD of `a` and `b` is "infinity" -- not 0, as math.gcd(0, 0)
        returns.
    """
    a = _maybe_augment(a)
    if not isinstance(a, Num):
        raise TypeError(f"Cannot convert {a} to Num.")
    b = _maybe_augment(b)
    if not isinstance(b, Num):
        raise TypeError(f"Cannot convert {b} to Num.")
    if a.value == _ERR or b.value == _ERR:
        return ERROR
    if a.value in (_NEG_INF, _INF, 0) and b.value in (_NEG_INF, _INF, 0):
        return INFINITY
    if a.is_infinite():
        return abs(b)
    if b.is_infinite():
        return abs(a)
    return Num(math.gcd(a.value, b.value))


INFINITY = Num(_INF)
NEGATIVE_INFINITY = Num(_NEG_INF)
ERROR = Num(_ERR)
