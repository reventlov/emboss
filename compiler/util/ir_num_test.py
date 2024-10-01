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

import unittest

from compiler.util import ir_num


class IrNumArithmeticTest(unittest.TestCase):

    def test_min_of_infinities(self):
        self.assertEqual(ir_num.INFINITY, min(ir_num.INFINITY, ir_num.INFINITY))
        self.assertEqual(3, min(ir_num.INFINITY, ir_num.Num(3)))

    def test_min_of_negative_infinities(self):
        self.assertEqual(ir_num.NEGATIVE_INFINITY, min(ir_num.NEGATIVE_INFINITY, 3))
        self.assertEqual(
            ir_num.NEGATIVE_INFINITY, min(ir_num.NEGATIVE_INFINITY, ir_num.INFINITY)
        )

    def test_max_of_negative_infinities(self):
        self.assertEqual(
            ir_num.NEGATIVE_INFINITY,
            max(ir_num.NEGATIVE_INFINITY, ir_num.NEGATIVE_INFINITY),
        )
        self.assertEqual(3, max(ir_num.NEGATIVE_INFINITY, ir_num.Num(3)))

    def test_max_of_infinities(self):
        self.assertEqual(
            ir_num.INFINITY, max(ir_num.INFINITY, ir_num.NEGATIVE_INFINITY)
        )
        self.assertEqual(ir_num.INFINITY, max(ir_num.INFINITY, 3))

    def test_init(self):
        self.assertEqual(0, ir_num.Num().value)
        self.assertEqual(3, ir_num.Num(3).value)
        self.assertEqual("infinity", ir_num.Num("infinity").value)
        self.assertEqual("-infinity", ir_num.Num("-infinity").value)
        self.assertEqual("error", ir_num.Num("error").value)

    def test_is_infinite(self):
        self.assertFalse(ir_num.Num(3).is_infinite())
        self.assertTrue(ir_num.Num("infinity").is_infinite())
        self.assertTrue(ir_num.Num("-infinity").is_infinite())
        self.assertFalse(ir_num.Num("error").is_infinite())

    def test_is_error(self):
        self.assertFalse(ir_num.Num(3).is_error())
        self.assertFalse(ir_num.Num("infinity").is_error())
        self.assertFalse(ir_num.Num("-infinity").is_error())
        self.assertTrue(ir_num.Num("error").is_error())

    def test_is_integer(self):
        self.assertTrue(ir_num.Num(3).is_integer())
        self.assertFalse(ir_num.Num("infinity").is_integer())
        self.assertFalse(ir_num.Num("-infinity").is_integer())
        self.assertFalse(ir_num.Num("error").is_integer())

    def test_sign(self):
        self.assertEqual(1, ir_num.Num(3).sign())
        self.assertEqual(0, ir_num.Num(0).sign())
        self.assertEqual(-1, ir_num.Num(-3).sign())
        self.assertEqual(1, ir_num.Num("infinity").sign())
        self.assertEqual(-1, ir_num.Num("-infinity").sign())
        with self.assertRaises(ValueError):
            ir_num.Num("error").sign()

    def test_bool(self):
        self.assertTrue(ir_num.Num(3))
        self.assertFalse(ir_num.Num(0))
        self.assertTrue(ir_num.Num(-3))
        self.assertTrue(ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("-infinity"))
        with self.assertRaises(ValueError):
            bool(ir_num.Num("error"))

    def test_hash(self):
        self.assertNotEqual(hash(ir_num.Num(0)), hash(ir_num.INFINITY))

    def test_int(self):
        self.assertEqual(3, int(ir_num.Num(3)))
        with self.assertRaises(ValueError):
            int(ir_num.INFINITY)
        with self.assertRaises(ValueError):
            int(ir_num.NEGATIVE_INFINITY)
        with self.assertRaises(ValueError):
            int(ir_num.ERROR)

    def test_eq(self):
        self.assertTrue(ir_num.Num(3) == ir_num.Num(3))
        self.assertTrue(ir_num.Num(3) == 3)
        self.assertTrue(3 == ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) == ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) == 3)
        self.assertFalse(2 == ir_num.Num(3))
        self.assertTrue(ir_num.Num("infinity") == ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("infinity") == "infinity")
        self.assertTrue(ir_num.Num("-infinity") == ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("error") == ir_num.Num("error"))
        self.assertFalse(ir_num.Num("infinity") == ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("infinity") == ir_num.Num("error"))
        self.assertFalse(ir_num.Num("infinity") == ir_num.Num(-2))
        self.assertFalse(ir_num.Num("-infinity") == ir_num.Num("error"))
        self.assertFalse(ir_num.Num("-infinity") == ir_num.Num(0))
        self.assertFalse(ir_num.Num("error") == ir_num.Num(2))

    def test_ne(self):
        self.assertFalse(ir_num.Num(3) != ir_num.Num(3))
        self.assertFalse(ir_num.Num(3) != 3)
        self.assertFalse(3 != ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) != ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) != 3)
        self.assertTrue(2 != ir_num.Num(3))
        self.assertFalse(ir_num.Num("infinity") != ir_num.Num("infinity"))
        self.assertFalse(ir_num.Num("infinity") != "infinity")
        self.assertFalse(ir_num.Num("-infinity") != ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("error") != ir_num.Num("error"))
        self.assertTrue(ir_num.Num("infinity") != ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("infinity") != ir_num.Num("error"))
        self.assertTrue(ir_num.Num("infinity") != ir_num.Num(-2))
        self.assertTrue(ir_num.Num("-infinity") != ir_num.Num("error"))
        self.assertTrue(ir_num.Num("-infinity") != ir_num.Num(0))
        self.assertTrue(ir_num.Num("error") != ir_num.Num(2))

    def test_lt(self):
        self.assertFalse(ir_num.Num(3) < ir_num.Num(3))
        self.assertFalse(ir_num.Num(3) < 3)
        self.assertFalse(3 < ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) < ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) < 3)
        self.assertTrue(2 < ir_num.Num(3))
        self.assertFalse(ir_num.Num("infinity") < ir_num.Num("infinity"))
        self.assertFalse(ir_num.Num("-infinity") < ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("infinity") < ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("-infinity") < ir_num.Num("infinity"))
        self.assertFalse(ir_num.Num("infinity") < ir_num.Num(-2))
        self.assertTrue(ir_num.Num("-infinity") < ir_num.Num(0))
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") < ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("infinity") < ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("-infinity") < ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") < ir_num.Num(2)

    def test_le(self):
        self.assertFalse(ir_num.Num(4) <= ir_num.Num(3))
        self.assertFalse(ir_num.Num(4) <= 3)
        self.assertFalse(4 <= ir_num.Num(3))
        self.assertTrue(ir_num.Num(3) <= ir_num.Num(3))
        self.assertTrue(ir_num.Num(3) <= 3)
        self.assertTrue(3 <= ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) <= ir_num.Num(3))
        self.assertTrue(ir_num.Num(2) <= 3)
        self.assertTrue(2 <= ir_num.Num(3))
        self.assertTrue(ir_num.Num("infinity") <= ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("-infinity") <= ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("infinity") <= ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("-infinity") <= ir_num.Num("infinity"))
        self.assertFalse(ir_num.Num("infinity") <= ir_num.Num(-2))
        self.assertTrue(ir_num.Num("-infinity") <= ir_num.Num(0))
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") <= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("infinity") <= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("-infinity") <= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") <= ir_num.Num(2)

    def test_gt(self):
        self.assertTrue(ir_num.Num(4) > ir_num.Num(3))
        self.assertTrue(ir_num.Num(4) > 3)
        self.assertTrue(4 > ir_num.Num(3))
        self.assertFalse(ir_num.Num(3) > ir_num.Num(3))
        self.assertFalse(ir_num.Num(3) > 3)
        self.assertFalse(3 > ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) > ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) > 3)
        self.assertFalse(2 > ir_num.Num(3))
        self.assertFalse(ir_num.Num("infinity") > ir_num.Num("infinity"))
        self.assertFalse(ir_num.Num("-infinity") > ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("infinity") > ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("-infinity") > ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("infinity") > ir_num.Num(-2))
        self.assertFalse(ir_num.Num("-infinity") > ir_num.Num(0))
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") > ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("infinity") > ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("-infinity") > ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") > ir_num.Num(2)

    def test_ge(self):
        self.assertTrue(ir_num.Num(3) >= ir_num.Num(3))
        self.assertTrue(ir_num.Num(3) >= 3)
        self.assertTrue(3 >= ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) >= ir_num.Num(3))
        self.assertFalse(ir_num.Num(2) >= 3)
        self.assertFalse(2 >= ir_num.Num(3))
        self.assertTrue(ir_num.Num("infinity") >= ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("-infinity") >= ir_num.Num("-infinity"))
        self.assertTrue(ir_num.Num("infinity") >= ir_num.Num("-infinity"))
        self.assertFalse(ir_num.Num("-infinity") >= ir_num.Num("infinity"))
        self.assertTrue(ir_num.Num("infinity") >= ir_num.Num(-2))
        self.assertFalse(ir_num.Num("-infinity") >= ir_num.Num(0))
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") >= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("infinity") >= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("-infinity") >= ir_num.Num("error")
        with self.assertRaises(ArithmeticError):
            ir_num.Num("error") >= ir_num.Num(2)

    def test_neg(self):
        self.assertEqual(-3, -ir_num.Num(3))
        self.assertEqual(0, -ir_num.Num(0))
        self.assertEqual(3, -ir_num.Num(-3))
        self.assertEqual("infinity", -ir_num.NEGATIVE_INFINITY)
        self.assertEqual("-infinity", -ir_num.INFINITY)
        self.assertEqual("error", -ir_num.ERROR)

    def test_pos(self):
        self.assertEqual(-3, +ir_num.Num(-3))
        self.assertEqual(0, +ir_num.Num(0))
        self.assertEqual(3, +ir_num.Num(3))
        self.assertEqual("infinity", +ir_num.INFINITY)
        self.assertEqual("-infinity", +ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", +ir_num.ERROR)

    def test_abs(self):
        self.assertEqual(3, abs(ir_num.Num(-3)))
        self.assertEqual(0, abs(ir_num.Num(0)))
        self.assertEqual(3, abs(ir_num.Num(3)))
        self.assertEqual("infinity", abs(ir_num.INFINITY))
        self.assertEqual("infinity", abs(ir_num.NEGATIVE_INFINITY))
        self.assertEqual("error", abs(ir_num.ERROR))

    def test_add(self):
        self.assertEqual(3, ir_num.Num(-3) + 6)
        self.assertEqual(5, ir_num.Num(-2) + ir_num.Num(7))
        self.assertEqual(4, 1 + ir_num.Num(3))
        self.assertEqual("infinity", ir_num.INFINITY + 5)
        self.assertEqual("infinity", ir_num.INFINITY + -5)
        self.assertEqual("infinity", -5 + ir_num.INFINITY)
        self.assertEqual("infinity", ir_num.INFINITY + ir_num.INFINITY)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY + 1)
        self.assertEqual("-infinity", -1 + ir_num.NEGATIVE_INFINITY)
        self.assertEqual(
            "-infinity", ir_num.NEGATIVE_INFINITY + ir_num.NEGATIVE_INFINITY
        )
        self.assertEqual("error", ir_num.ERROR + 2)
        self.assertEqual("error", 2 + ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR + ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR + ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR + ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY + ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY + ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY + ir_num.INFINITY)
        self.assertEqual("error", ir_num.INFINITY + ir_num.NEGATIVE_INFINITY)

    def test_sub(self):
        self.assertEqual(-9, ir_num.Num(-3) - 6)
        self.assertEqual(-5, ir_num.Num(2) - ir_num.Num(7))
        self.assertEqual(2, 3 - ir_num.Num(1))
        self.assertEqual("infinity", ir_num.INFINITY - 5)
        self.assertEqual("infinity", ir_num.INFINITY - -5)
        self.assertEqual("infinity", -5 - ir_num.NEGATIVE_INFINITY)
        self.assertEqual("infinity", ir_num.INFINITY - ir_num.NEGATIVE_INFINITY)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY - 1)
        self.assertEqual("-infinity", -1 - ir_num.INFINITY)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY - ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR - 2)
        self.assertEqual("error", 2 - ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR - ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR - ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR - ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY - ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY - ir_num.ERROR)
        self.assertEqual("error", ir_num.INFINITY - ir_num.INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY - ir_num.NEGATIVE_INFINITY)

    def test_mul(self):
        self.assertEqual(-18, ir_num.Num(-3) * 6)
        self.assertEqual(14, ir_num.Num(2) * ir_num.Num(7))
        self.assertEqual(6, 3 * ir_num.Num(2))
        self.assertEqual("infinity", ir_num.INFINITY * 5)
        self.assertEqual("infinity", -5 * ir_num.NEGATIVE_INFINITY)
        self.assertEqual("infinity", ir_num.INFINITY * ir_num.INFINITY)
        self.assertEqual(
            "infinity", ir_num.NEGATIVE_INFINITY * ir_num.NEGATIVE_INFINITY
        )
        self.assertEqual("-infinity", ir_num.INFINITY * -5)
        self.assertEqual("-infinity", ir_num.INFINITY * ir_num.NEGATIVE_INFINITY)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY * 2)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY * ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR * 2)
        self.assertEqual("error", 2 * ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR * ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR * ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR * ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY * ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY * ir_num.ERROR)

    def test_mod(self):
        self.assertEqual(4, ir_num.Num(-8) % 6)
        self.assertEqual(-2, ir_num.Num(-8) % -6)
        self.assertEqual(1, ir_num.Num(7) % ir_num.Num(2))
        self.assertEqual(-1, ir_num.Num(7) % ir_num.Num(-2))
        self.assertEqual(3, 11 % ir_num.Num(4))
        self.assertEqual(-1, 11 % ir_num.Num(-4))
        self.assertEqual(17, 17 % ir_num.INFINITY)
        self.assertEqual(0, 0 % ir_num.INFINITY)
        self.assertEqual(-17, -17 % ir_num.INFINITY)
        self.assertEqual("error", 17 % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", 0 % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", -17 % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY % 5)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY % 5)
        self.assertEqual("error", ir_num.INFINITY % ir_num.INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY % ir_num.INFINITY)
        self.assertEqual("error", ir_num.INFINITY % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.ERROR % 2)
        self.assertEqual("error", 2 % ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR % ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR % ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR % ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY % ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY % ir_num.ERROR)

    def test_floordiv(self):
        self.assertEqual(-2, ir_num.Num(-8) // 6)
        self.assertEqual(1, ir_num.Num(-8) // -6)
        self.assertEqual(3, ir_num.Num(7) // ir_num.Num(2))
        self.assertEqual(-4, ir_num.Num(7) // ir_num.Num(-2))
        self.assertEqual(2, 11 // ir_num.Num(4))
        self.assertEqual(-3, 11 // ir_num.Num(-4))
        self.assertEqual(0, 17 // ir_num.INFINITY)
        self.assertEqual(0, 0 // ir_num.INFINITY)
        self.assertEqual(0, -17 // ir_num.INFINITY)
        self.assertEqual(0, 17 // ir_num.NEGATIVE_INFINITY)
        self.assertEqual(0, 0 // ir_num.NEGATIVE_INFINITY)
        self.assertEqual(0, -17 // ir_num.NEGATIVE_INFINITY)
        self.assertEqual("infinity", ir_num.INFINITY // 5)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY // 5)
        self.assertEqual("-infinity", ir_num.INFINITY // -5)
        self.assertEqual("infinity", ir_num.NEGATIVE_INFINITY // -5)
        self.assertEqual("error", ir_num.INFINITY // ir_num.INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY // ir_num.INFINITY)
        self.assertEqual("error", ir_num.INFINITY // ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY // ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.ERROR // 2)
        self.assertEqual("error", 2 // ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR // ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR // ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR // ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY // ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY // ir_num.ERROR)

    def test_pow(self):
        self.assertEqual(262144, ir_num.Num(-8) ** 6)
        self.assertEqual(-32768, ir_num.Num(-8) ** 5)
        self.assertEqual("error", ir_num.Num(-8) ** -6)
        self.assertEqual(49, ir_num.Num(7) ** ir_num.Num(2))
        self.assertEqual("error", ir_num.Num(7) ** ir_num.Num(-1))
        self.assertEqual(14641, 11 ** ir_num.Num(4))
        self.assertEqual("error", 11 ** ir_num.Num(-4))
        self.assertEqual("infinity", 17**ir_num.INFINITY)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY**1)
        self.assertEqual("infinity", ir_num.NEGATIVE_INFINITY**2)
        self.assertEqual("-infinity", ir_num.NEGATIVE_INFINITY**3)
        self.assertEqual("infinity", ir_num.NEGATIVE_INFINITY**4)
        self.assertEqual(0, 0**ir_num.INFINITY)
        self.assertEqual(1, 1**ir_num.INFINITY)
        self.assertEqual("error", (-1) ** ir_num.INFINITY)
        self.assertEqual(1, (-1) ** ir_num.Num(0))
        self.assertEqual("error", 0 ** ir_num.Num(0))
        self.assertEqual(1, 1 ** ir_num.Num(0))
        self.assertEqual(1, 2 ** ir_num.Num(0))
        self.assertEqual(1, ir_num.INFINITY ** ir_num.Num(0))
        self.assertEqual(1, ir_num.NEGATIVE_INFINITY ** ir_num.Num(0))
        self.assertEqual("error", ir_num.INFINITY**ir_num.NEGATIVE_INFINITY)
        self.assertEqual("infinity", ir_num.INFINITY**ir_num.INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY**ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY**ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR**2)
        self.assertEqual("error", 2**ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR**ir_num.ERROR)
        self.assertEqual("error", ir_num.ERROR**ir_num.INFINITY)
        self.assertEqual("error", ir_num.ERROR**ir_num.NEGATIVE_INFINITY)
        self.assertEqual("error", ir_num.INFINITY**ir_num.ERROR)
        self.assertEqual("error", ir_num.NEGATIVE_INFINITY**ir_num.ERROR)

    def test_gcd(self):
        self.assertEqual(2, ir_num.gcd(-8, 6))
        self.assertEqual(2, ir_num.gcd(-8, -6))
        self.assertEqual(12, ir_num.gcd(-12, 0))
        self.assertEqual(12, ir_num.gcd(12, 0))
        self.assertEqual(8, ir_num.gcd(-8, ir_num.INFINITY))
        self.assertEqual(8, ir_num.gcd(8, ir_num.INFINITY))
        self.assertEqual(8, ir_num.gcd(-8, ir_num.NEGATIVE_INFINITY))
        self.assertEqual(8, ir_num.gcd(8, ir_num.NEGATIVE_INFINITY))
        self.assertEqual(8, ir_num.gcd(ir_num.INFINITY, -8))
        self.assertEqual(8, ir_num.gcd(ir_num.INFINITY, 8))
        self.assertEqual(8, ir_num.gcd(ir_num.NEGATIVE_INFINITY, -8))
        self.assertEqual(8, ir_num.gcd(ir_num.NEGATIVE_INFINITY, 8))
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(0, 0))
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(0, ir_num.INFINITY))
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(0, ir_num.NEGATIVE_INFINITY))
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(ir_num.INFINITY, 0))
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(ir_num.NEGATIVE_INFINITY, 0))
        self.assertEqual(
            ir_num.INFINITY, ir_num.gcd(ir_num.INFINITY, ir_num.NEGATIVE_INFINITY)
        )
        self.assertEqual(
            ir_num.INFINITY,
            ir_num.gcd(ir_num.NEGATIVE_INFINITY, ir_num.NEGATIVE_INFINITY),
        )
        self.assertEqual(ir_num.INFINITY, ir_num.gcd(ir_num.INFINITY, ir_num.INFINITY))
        self.assertEqual(
            ir_num.INFINITY, ir_num.gcd(ir_num.NEGATIVE_INFINITY, ir_num.INFINITY)
        )


if __name__ == "__main__":
    unittest.main()
