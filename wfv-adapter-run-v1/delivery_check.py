"""Delivery leg (D) of the frozen adapter test v1: run the packaged adapter the way the node and the runner do.

Usage (kit venv): python delivery_check.py <kit_dir> <packaged.wasm> <adapter_dir>
Writes delivery.json next to this file. Gating checks per the frozen README:
one HEX line per run, three repeats bit-identical, runner bits == direct bits, WASM orders >= 9/10 pairs like PyTorch.
"""
import json, re, struct, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parent
KIT, WASM, ADAPTER = (Path(a).resolve() for a in sys.argv[1:4])
BASE = "answerdotai/ModernBERT-base"
HEX = re.compile(r"(?m)^HEX\s*:\s*0x([0-9a-fA-F]{8})\b")

import torch
torch.set_default_device("cpu")
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel

tok = AutoTokenizer.from_pretrained(BASE)


def ids(prompt, answer):
    return tok(f"### Task:\n{prompt}\n\n### Answer:\n{answer}", truncation=True, max_length=512)["input_ids"]


def f32(h):
    return struct.unpack(">f", bytes.fromhex(h))[0]


def run_wasm(tokens):
    """Same invocation as cmd/adapterrunner: wasmtime run --dir <tmp>::/in <wasm> /in/input.json 1."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "input.json").write_text(json.dumps({"input_ids": tokens, "attention_mask": [1] * len(tokens)}))
        t0 = time.perf_counter()
        p = subprocess.run(["/usr/bin/time", "-l", "wasmtime", "run", "--dir", f"{d}::/in", str(WASM), "/in/input.json", "1"],
                           capture_output=True, text=True, timeout=900)
        dt = time.perf_counter() - t0
    rss = re.search(r"(\d+)\s+maximum resident set size", p.stderr)
    return {"hex": HEX.findall(p.stdout), "rc": p.returncode, "seconds": round(dt, 2),
            "peak_rss_mb": round(int(rss.group(1)) / 2**20) if rss else None, "n_tokens": len(tokens),
            "stderr_tail": p.stderr.strip().splitlines()[-1:] if p.returncode else []}


def main():
    pairs = [json.loads(l) for l in open(RUN / "test.jsonl")][::6][:10]  # 10 held-out pairs across F4/F6/F7
    model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=1, dtype=torch.float32, attn_implementation="eager")
    model = PeftModel.from_pretrained(model, str(ADAPTER)).merge_and_unload().float().eval()

    def tscore(t):
        with torch.inference_mode():
            return model(input_ids=torch.tensor([t]), attention_mask=torch.ones(1, len(t), dtype=torch.long)).logits.reshape(-1)[0].item()

    runs, agree, rows = [], 0, []
    for p in pairs:
        tc, tr = ids(p["prompt"], p["chosen"]), ids(p["prompt"], p["rejected"])
        wc, wr = run_wasm(tc), run_wasm(tr)
        runs += [wc, wr]
        ok = len(wc["hex"]) == 1 and len(wr["hex"]) == 1
        w_pref = ok and f32(wc["hex"][0]) > f32(wr["hex"][0])
        sc, sr = tscore(tc), tscore(tr)
        t_pref = sc > sr
        agree += ok and (w_pref == t_pref)
        rows.append({"torch": [sc, sr], "wasm": [f32(wc["hex"][0]) if wc["hex"] else None,
                     f32(wr["hex"][0]) if wr["hex"] else None], "same_order": bool(ok and w_pref == t_pref)})
        print("pair", len(rows), rows[-1], wc["seconds"], "s", flush=True)

    t0 = ids(pairs[0]["prompt"], pairs[0]["chosen"])
    repeats = [run_wasm(t0) for _ in range(3)]
    runs += repeats
    long_text = ids(pairs[0]["prompt"], " ".join([pairs[0]["chosen"]] * 8))  # truncated to 512 tokens
    long_run = run_wasm(long_text)
    runs.append(long_run)

    # runner: same bits as the direct run for two inputs
    srv = subprocess.Popen([str(KIT / "adapterrunner")], env={"ADAPTER_WASM": str(WASM), "ADAPTER_RUNNER_LISTEN": "127.0.0.1:18080",
                           "ADAPTER_RUNNER_TIMEOUT": "900s", "PATH": "/opt/homebrew/bin:/usr/bin:/bin"},
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen("http://127.0.0.1:18080/healthz", timeout=2)
                break
            except Exception:
                time.sleep(1)
        t1 = ids(pairs[1]["prompt"], pairs[1]["rejected"])
        req = json.dumps({"batch": [{"tokens": t0}, {"tokens": t1}]}).encode()
        t_start = time.perf_counter()
        resp = json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:18080/runnable", data=req,
                          headers={"Content-Type": "application/json"}), timeout=1800).read())
        runner_seconds = round(time.perf_counter() - t_start, 2)
    finally:
        srv.terminate()
    direct = [int(repeats[0]["hex"][0], 16), int(runs[3]["hex"][0], 16)]  # runs[3] = pair 2 rejected
    runner_bits = [r.get("score") for r in resp["results"]]

    checks = {
        "one_hex_line_every_run": all(len(r["hex"]) == 1 and r["rc"] == 0 for r in runs),
        "three_repeats_bit_identical": len({tuple(r["hex"]) for r in repeats}) == 1,
        "runner_bits_equal_direct": runner_bits == direct,
        "wasm_torch_same_order": f"{agree}/10",
        "wasm_torch_same_order_pass": agree >= 9,
    }
    checks["delivery_pass"] = all(v for k, v in checks.items() if k != "wasm_torch_same_order")
    out = {"checks": checks, "package_bytes": WASM.stat().st_size,
           "latency_seconds": {"median_short": sorted(r["seconds"] for r in runs[:20])[10], "max_short": max(r["seconds"] for r in runs[:20]),
                               "first_run": runs[0]["seconds"], "512_tokens": long_run["seconds"], "runner_batch_of_2": runner_seconds},
           "peak_rss_mb_max": max(r["peak_rss_mb"] or 0 for r in runs), "long_run_tokens": long_run["n_tokens"],
           "runner_bits": runner_bits, "direct_bits": direct, "pairs": rows, "runs": runs}
    (RUN / "delivery.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"checks": checks, "latency_seconds": out["latency_seconds"], "peak_rss_mb_max": out["peak_rss_mb_max"],
                      "package_bytes": out["package_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
