// Copyright 2019 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// This file contains various utility routines for manipulating values at a low
// level, such as byte swaps and safe casts.
#ifndef EMBOSS_RUNTIME_CPP_EMBOSS_BIT_UTIL_H_
#define EMBOSS_RUNTIME_CPP_EMBOSS_BIT_UTIL_H_

#include <climits>
#include <cstdint>
#include <type_traits>

#include "runtime/cpp/emboss_defines.h"

namespace emboss {
namespace support {

// Where possible, it is best to use byte swap builtins, but if they are not
// available ByteSwap can fall back to portable code.
inline constexpr ::std::uint8_t ByteSwap(::std::uint8_t x) { return x; }
inline constexpr ::std::uint16_t ByteSwap(::std::uint16_t x) {
#ifdef EMBOSS_BYTESWAP16
  return EMBOSS_BYTESWAP16(x);
#else
  return (x << 8) | (x >> 8);
#endif
}
inline constexpr ::std::uint32_t ByteSwap(::std::uint32_t x) {
#ifdef EMBOSS_BYTESWAP32
  return EMBOSS_BYTESWAP32(x);
#else
  return (static_cast</**/ ::std::uint32_t>(
              ByteSwap(static_cast</**/ ::std::uint16_t>(x)))
          << 16) |
         ByteSwap(static_cast</**/ ::std::uint16_t>(x >> 16));
#endif
}
inline constexpr ::std::uint64_t ByteSwap(::std::uint64_t x) {
#ifdef EMBOSS_BYTESWAP64
  return EMBOSS_BYTESWAP64(x);
#else
  return (static_cast</**/ ::std::uint64_t>(
              ByteSwap(static_cast</**/ ::std::uint32_t>(x)))
          << 32) |
         ByteSwap(static_cast</**/ ::std::uint32_t>(x >> 32));
#endif
}

// Masks the given value to the given number of bits.
template <typename T>
inline constexpr T MaskToNBits(T value, unsigned bits) {
  static_assert(!::std::is_signed<T>::value,
                "MaskToNBits only works on unsigned values.");
  return bits < sizeof value * 8 ? value & ((static_cast<T>(1) << bits) - 1)
                                 : value;
}

template <typename T>
inline constexpr bool IsPowerOfTwo(T value) {
  // This check relies on an old bit-counting trick; x & (x - 1) always has one
  // fewer bit set to 1 than x (if x is nonzero), and powers of 2 always have
  // exactly one 1 bit, thus x & (x - 1) == 0 if x is a power of 2.
  return value > 0 && (value & (value - 1)) == 0;
}

template <typename T,
          ::std::enable_if_t<!::std::is_signed<T>::value, bool> = true>
inline constexpr T TwosComplementCast(T value) {
  return value;
}

template <typename T,
          ::std::enable_if_t</**/ ::std::is_signed<T>::value, bool> = true>
inline constexpr T TwosComplementCast(
    typename ::std::make_unsigned<T>::type value) {
#if EMBOSS_SYSTEM_IS_TWOS_COMPLEMENT
  // static_cast from unsigned to signed is implementation-defined when the
  // value does not fit in the signed type (in this case, when the final value
  // should be negative).  Most implementations use a reasonable definition, so
  // on most systems we can just cast.
  return static_cast<T>(value);
#else
  using U = typename ::std::make_unsigned<T>::type;
  // Otherwise, in order to convert without running into implementation-defined
  // behavior, first mask out the sign bit.  This results in (final result MOD
  // 2 ** (width of int in bits - 1)).  That value can be safely converted to
  // the signed T.
  //
  // Finally, if the sign bit was set, subtract (2 ** (width of int in bits -
  // 2)) twice.
  U sign_bit = static_cast<U>(1) << (sizeof(U) * CHAR_BIT - 1);
  U mask = sign_bit - 1;
  T data_mod2_to_n = static_cast<T>(mask & value);
  T result_sign_bit = static_cast<T>((value & sign_bit) >> 1);
  return data_mod2_to_n - result_sign_bit - result_sign_bit;
#endif
}

}  // namespace support
}  // namespace emboss

#endif  // EMBOSS_RUNTIME_CPP_EMBOSS_BIT_UTIL_H_
