# MACRO_ECONOMIC_INDICATOR comparator module v1 (bounty #94, Part 2)

A comparator module for the `MACRO_ECONOMIC_INDICATOR` family: `src/lib.rs`, built as `macro_comparator.wasm` (2,527 bytes, `#![no_std]`, `wasm32-unknown-unknown`, zero imports).

- **sha256:** `30746352279c9054027aa3ebd807d124f049f0f05264a1f6bd75c30ba2d7112b`
- **keccak256 (the registered hash):** `0x7c014871e3220407cd5b59edf74562f311c74d97b4343d2a65e058f8d85b6805`

**Exports:**
- `imw_score_deterministic(truth: i64, miner: i64, spec_ptr: i32) -> i64`
- `imw_alloc(i32) -> i32`, which returns a 64-byte static buffer
- `imw_free(i32, i32)`

**Rule:** the reference rule from "Comparator modules" in [Build an Evaluator Adapter](https://anjoman.ai/docs/scoring/build-a-scoring-module), matching the kit's Python golden `comparator_core` (`telegraph-wasm-baseline` @`992f265`, SHA-256 pinned in the test):
- The code is read at 32-bit width; unknown codes and PassFail mean Exact.
- AbsTol uses `|miner − truth|`. RelTol uses `|miner − truth| × 10000 / max(|truth|, 1)`. Both are computed in i128 and clamped to i64 max.
- A tolerance ≤ 0 scores 10000 only when that error is 0. For RelTol this is the truncated basis-point error, as in the kit, so 80,000 against 79,999 scores 10000.
- Otherwise the score is `10000.saturating_mul(2·tol − err) / (2·tol)`, and 0 once `err ≥ 2·tol`.
- Release builds have `overflow-checks` on, so any overflow I missed traps instead of wrapping.

**Test** (`test_comparator.py`, run on the actual `.wasm` through wasmtime with no host imports):

| Check | Result |
|---|---|
| Frozen October grid, 17,680 vectors | Matches the kit golden on all. The grid itself differs from the golden on 240, which the golden decides: 98 where the docs' saturating multiply applies at tolerance ≥ ~4.6e14, and 142 RelTol cases with tolerance ≤ 0. zkasuran's canonical comparator agrees with the golden on all but 3, at truth = i64 min, outside the node's domain. |
| 20,000 cases shaped like the node's battery (truth ±1…1e18, every code, tolerances −5…1e12, miners exact, ±1, half-score, at, inside and past the 2× window) | 0 mismatches against the kit golden. 0 of 19,735 against zkasuran's CRYPTO_PRICE comparator (keccak `3464c975…`, canonical on the node after its 1,120-case battery). The 265 cases with the miner clamped to i64 extremes aren't compared. |
| 776 i64-extreme probes | All in [0, 10000]; 0 differ from the kit golden. 123 differ from zkasuran, all outside the node's domain. |
| Second run in a fresh instance, then reversed order in a reused instance | Bit-identical over 38,456 cases |

**Endpoint** (`app/lambda_function.py`, AWS Lambda `telegraph-macro-comparator`, `aws/deploy.sh`):
- `GET /module.wasm` serves the exact registered bytes. This is the `wasmUrl`, since the repository is private.
- `POST /runnable` takes the node's batch request, `{"batch": [{"ground_truth_value", "miner_value", "spec": [code, tol]}, …]}` with at most 100 questions. It scores each question with the same bytes under wasmtime, in a fresh instance per request, and returns `{"results": [{"score": bps} | {"error": …}]}`.
- `test_endpoint.py` checks the served bytes, batch scores against the golden, malformed questions and oversize batches.

**State on 2026-11-06:**
- Sireadell's comparator (reg 115) is pending `awaiting_compatible_material`. The macro pool has 3 contributors and the node needs 5, so any comparator waits.
- The Issue counts a part "once your module passes the network's checks", not only the first module to pass.
- No comparator is live, so `MACRO_ECONOMIC_INDICATOR_GENERAL` is scored by the GENERIC judgment fallback today, and our World Bank truth source isn't used yet.

**Register (the user's signed step).** You need about 5.3 MACHINA for the $5 bond, plus Sepolia gas. There's no MACHINA faucet: mint test USDC and swap it on the Sepolia MACHINA/USDC pool ("Getting test tokens" on [Addresses & Parameters](https://anjoman.ai/docs/protocol/addresses-and-params#getting-test-tokens)). Hash the bytes as served:

```sh
export DIAMOND=0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b RPC=https://ethereum-sepolia-rpc.publicnode.com
export MACHINA=0xd68305cA83C7AF42A4F720144E7416fB53F8AaF4
export URL=https://rsskgwyru5xsoojm6q6m4tbxo40oyrgy.lambda-url.eu-north-1.on.aws
export WASM_URL=$URL/module.wasm RUNNABLE=$URL/runnable FEE=<your payout address>
export WASM_HASH=$(curl -s $WASM_URL | cast keccak)   # must be 0x7c014871…6805
cast send $MACHINA "approve(address,uint256)" $DIAMOND 20000000000000000000 --rpc-url $RPC --private-key $KEY
cast call $DIAMOND "registerWasm(bytes32,string,string,address,string)(uint256)" $WASM_HASH $WASM_URL MACRO_ECONOMIC_INDICATOR $FEE $RUNNABLE --from $(cast wallet address --private-key $KEY) --rpc-url $RPC
cast send $DIAMOND "registerWasm(bytes32,string,string,address,string)(uint256)" $WASM_HASH $WASM_URL MACRO_ECONOMIC_INDICATOR $FEE $RUNNABLE --rpc-url $RPC --private-key $KEY
```

The `cast call` line is the free dry run; it returns the registration id or the revert reason. Follow the result at `https://devnode.telegraphprotocol.com/api/wasm?resolve=MACRO_ECONOMIC_INDICATOR`. The bond comes back in full on deregistering.

**Limits:**
- The endpoint has to stay up until the registration leaves pending.
- Passing locally doesn't prove the node accepts it; its 100-case pre-check and 1,260-case Stage 2 decide.
