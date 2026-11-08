"""Score a trained run on the frozen held-out sets, with per-kind breakdowns.

Sets: data/test_format.jsonl (unseen F4 memo format), data/test_kind.jsonl (unseen kinds K2, K8), and material v1's
204 pairs (an earlier, separate generator; never trained on). Frozen go rule (README): format >= 0.75, kind >= 0.70,
v1 >= 0.65.
Usage (from kit/): ../.venv/bin/python ../eval_heldout.py ../runs/v1/adapter
"""
import json, sys
from collections import defaultdict
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from float_runtime.train_adapter import DEFAULT_BASE, PairCollator, _reward, read_pairs_jsonl

HERE = Path(__file__).resolve().parent
RULE = {"test_format": 0.75, "test_kind": 0.70, "material_v1": 0.65}


def sets():
    out = {}
    for s in ("test_format", "test_kind"):
        meta = [json.loads(l) for l in open(HERE / "data" / f"{s}.meta.jsonl")]
        out[s] = (read_pairs_jsonl(HERE / "data" / f"{s}.jsonl"), [m["kind"] for m in meta])
    v1 = HERE.parent / "telegraph-s2-sanctions-material-v1"
    meta = [json.loads(l) for l in open(v1 / "meta.jsonl")]
    out["material_v1"] = (read_pairs_jsonl(v1 / "material.jsonl"), [f"{m['type']}/{m['family']}" for m in meta])
    return out


def main(adapter_dir):
    tok = AutoTokenizer.from_pretrained(adapter_dir)
    base = AutoModelForSequenceClassification.from_pretrained(DEFAULT_BASE, num_labels=1, torch_dtype=torch.float32,
                                                              attn_implementation="eager")
    base.config.pad_token_id = tok.pad_token_id
    model = PeftModel.from_pretrained(base, adapter_dir).eval()
    report = {}
    for name, (pairs, kinds) in sets().items():
        assert len(pairs) == len(kinds), name
        diffs = []
        coll = PairCollator(tok, 512)
        with torch.no_grad():
            for i in range(0, len(pairs), 8):
                b = coll(pairs[i:i + 8])
                rc = _reward(model, b["chosen_input_ids"], b["chosen_attention_mask"])
                rr = _reward(model, b["rejected_input_ids"], b["rejected_attention_mask"])
                diffs += (rc - rr).float().tolist()
        by = defaultdict(list)
        for d, k in zip(diffs, kinds):
            by[k].append(d > 0)
        acc = sum(d > 0 for d in diffs) / len(diffs)
        report[name] = {"n": len(diffs), "accuracy": round(acc, 4), "rule": RULE[name], "pass": acc >= RULE[name],
                        "by_kind": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(by.items())}}
        print(name, json.dumps(report[name]), flush=True)
    report["go"] = all(r["pass"] for r in report.values() if isinstance(r, dict))
    (Path(adapter_dir).parent / "heldout.json").write_text(json.dumps(report, indent=1))
    print("GO" if report["go"] else "STOP")


if __name__ == "__main__":
    main(sys.argv[1])
