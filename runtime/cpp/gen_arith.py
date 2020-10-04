#!/usr/bin/python3
OVERLOADS = 64
for i in range(5, OVERLOADS + 1):
  print("""
template <typename T>
static inline constexpr T Do({0}) {{
  return Do(Do({1}), Do({2}));
}}""".format(
    ", ".join(["T v{}".format(n) for n in range(i)]),
    ", ".join(["v{}".format(n) for n in range(i // 2)]),
    ", ".join(["v{}".format(n) for n in range(i // 2, i)])))
print("""
template <typename T, typename... RestT>
static inline constexpr T Do({0}, RestT... rest) {{
  return Do(Do({1}), Do(v{2}, rest...));
}}""".format(
    ", ".join(["T v{}".format(n) for n in range(OVERLOADS + 1)]),
    ", ".join(["v{}".format(n) for n in range(OVERLOADS)]),
    OVERLOADS))
