"""Conformance test for the comparator .wasm, run through wasmtime with no host imports.

Oracles: the October frozen grid (17,680 vectors with expected scores), the kit's Python golden
`comparator_core` (telegraph-wasm-baseline @992f265, pinned by SHA-256), and zkasuran's
CRYPTO_PRICE comparator, which is canonical on the node after passing its 1,120-case battery.
Usage: python test_comparator.py target/wasm32-unknown-unknown/release/macro_comparator.wasm
"""
import hashlib, importlib.util, json, random, struct, sys
from pathlib import Path
import wasmtime

HERE = Path(__file__).parent
GRID = HERE.parent / "t2-launch-rule-v1" / "comparator-grid.json"
PROBES = HERE.parent / "t2-launch-run" / "oracle-overflow-probes.json"
GOLDEN = HERE / "oracle" / "kit_hybrid_992f265.py"
ZK = HERE / "oracle" / "zkasuran-CRYPTO_PRICE-3464c975.wasm"
assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == "0312dacfc7bfe8ac276d02a377bb23d81c03f1d3e6f56af341488dbbd220a9fe"
I64_MAX = (1 << 63) - 1


class Module:
    def __init__(self, path):
        self.engine = wasmtime.Engine()
        self.module = wasmtime.Module.from_file(self.engine, str(path))
        self.fresh()

    def fresh(self):
        self.store = wasmtime.Store(self.engine)
        inst = wasmtime.Instance(self.store, self.module, [])  # no imports provided: any import fails here
        ex = inst.exports(self.store)
        self.mem, self.alloc, self.free, self.score_fn = ex["memory"], ex["imw_alloc"], ex["imw_free"], ex["imw_score_deterministic"]

    def score(self, truth, miner, code, tol):
        p = self.alloc(self.store, 16)
        self.mem.write(self.store, struct.pack("<qq", code, tol), p)
        r = self.score_fn(self.store, truth, miner, p)
        self.free(self.store, p, 16)
        return r


def golden():
    spec = importlib.util.spec_from_file_location("kit_hybrid", GOLDEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    def ref(truth, miner, code, tol):
        c = struct.unpack("<i", struct.pack("<q", code)[:4])[0]  # read at 32-bit width
        return m.comparator_core(c if c in (0, 1, 2, 3) else 0, miner, truth, tol)  # unknown code -> Exact
    return ref


def battery(n, seed):
    """Cases shaped like the node's Stage 2 battery: truths 1..1e18 and negative, miners both sides."""
    rnd, out = random.Random(seed), []
    tols = [-5, 0, 1, 2, 10, 50, 100, 500, 1000, 2500, 10000, 10**6, 10**9, 10**12]
    for _ in range(n):
        truth = rnd.choice([1, -1]) * (10 ** rnd.randint(0, 18)) * rnd.randint(1, 9)
        truth = max(min(truth, 10**18), -10**18) or 1
        code, tol = rnd.randint(0, 3), rnd.choice(tols)
        w = 2 * abs(tol) * (abs(truth) // 10000 + 1 if code == 2 else 1)
        off = rnd.choice([0, 1, -1, w // 2, -(w // 2), w, -w, w - 1, -(w - 1), w + 1, -(w + 1), 3 * w, rnd.randint(-w - 5, w + 5)])
        out.append((truth, max(min(truth + off, I64_MAX), -I64_MAX - 1), code, tol))  # node values are i64
    return out


def main(path):
    raw = Path(path).read_bytes()
    mod, zk, ref = Module(path), Module(ZK), golden()
    imports = wasmtime.Module(mod.engine, raw).imports
    assert len(imports) == 0, imports
    exports = {e.name for e in wasmtime.Module(mod.engine, raw).exports}
    assert {"imw_score_deterministic", "imw_alloc", "imw_free", "memory"} <= exports, exports

    grid = json.loads(GRID.read_text())
    core = [(int(v["truth"]), int(v["miner"]), int(v["code_i64"]), int(v["tolerance_i64"]), v["expected_bps"])
            for v in grid["core_vectors"]]
    # The October grid was written from the docs' prose before any official code was pinned. Where it differs
    # from the kit golden (saturated 10000*(window-error) at huge tolerances; RelTol with tolerance <= 0 judged on
    # the truncated basis-point error, not raw equality), the kit golden decides, and zkasuran's canonical
    # comparator, which passed the node's battery, must agree with it too.
    diff = [c for c in core if ref(*c[:4]) != c[4]]
    kinds = {"saturated product": sum(c[3] > 0 for c in diff), "RelTol tolerance <= 0": sum(c[3] <= 0 for c in diff)}
    bad = [(c, mod.score(*c[:4])) for c in core if mod.score(*c[:4]) != ref(*c[:4])]
    print(f"frozen grid: {len(core)} vectors; {len(core) - len(diff)} where the grid agrees with the kit golden, "
          f"{len(diff)} where it doesn't {kinds}")
    assert not bad, bad[:5]
    zkd = [c for c in diff if ref(*c[:4]) != zk.score(*c[:4])]
    assert all(abs(c[0]) > 10**18 for c in zkd), zkd  # zkasuran differs only at truth = i64 min, outside the node domain
    print(f"  ours matches the kit golden on all of them; zkasuran's canonical comparator agrees on all but {len(zkd)} "
          f"(truth = i64 min, outside the node's 1..1e18 domain)")

    cases = battery(20000, 20261106)
    gm = sum(abs(mod.score(*c) - ref(*c)) > 0 for c in cases)
    inside = [c for c in cases if abs(c[1]) <= 4 * 10**18]  # zkasuran differs only where the miner was clamped to i64 max/min
    zm = sum(mod.score(*c) != zk.score(*c) for c in inside)
    print(f"battery-shaped cases: {len(cases)}; mismatches vs kit golden {gm}; vs zkasuran canonical {zm} of "
          f"{len(inside)} with |miner| <= 4e18 ({len(cases) - len(inside)} clamped to i64 extremes not compared)")
    assert gm == 0 and zm == 0

    probes = [(int(v["truth"]), int(v["miner"]), int(v["code_i64"]), int(v["tolerance_i64"]))
              for v in grid["mandatory_overflow_vectors"]]
    pg = sum(mod.score(*c) != ref(*c) for c in probes)
    pz = sum(mod.score(*c) != zk.score(*c) for c in probes)
    oob = sum(not 0 <= mod.score(*c) <= 10000 for c in probes)
    print(f"i64-extreme probes (outside the node's 1..1e18 domain): {len(probes)}; differ from kit golden {pg}, "
          f"from zkasuran {pz}; out of [0,10000]: {oob}")
    assert oob == 0 and pg == 0

    every = [c[:4] for c in core] + cases + probes
    first = [mod.score(*c) for c in every]
    mod.fresh()
    assert [mod.score(*c) for c in every] == first, "second run differs"
    assert [mod.score(*c) for c in reversed(every)] == first[::-1], "reused instance, reversed order differs"
    print(f"repeat and reversed runs over {len(every)} cases: bit-identical")
    print("bytes", len(raw), "sha256", hashlib.sha256(raw).hexdigest())
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1])
