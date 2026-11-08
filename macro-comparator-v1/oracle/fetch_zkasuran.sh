#!/bin/sh
# Third-party oracle for test_comparator.py: zkasuran's CRYPTO_PRICE comparator (registration 205 on the
# Telegraph devnode), fetched from its public pinned URL rather than redistributed here. Checks the hash.
set -e
cd "$(dirname "$0")"
curl -sfo zkasuran-CRYPTO_PRICE-3464c975.wasm \
  https://raw.githubusercontent.com/zkasuran/telegraph-catalog-miners/ade3352d1eb607f314ae6c7f7828bc1db0184502/comparators/CRYPTO_PRICE-3464c975.wasm
echo "f0b98f5004d0ef1eb663  (sha256 prefix expected)"; shasum -a 256 zkasuran-CRYPTO_PRICE-3464c975.wasm
