"""Shortcut judges for preference pairs (JSONL with prompt/chosen/rejected).

Each judge picks one answer per pair with a cheap rule. Accuracy far above 50%
means the set can be passed without the skill it is meant to measure.
Ties count as half right. Standard library only.
Usage: python3 judges.py file.jsonl [file.jsonl ...]
"""
import json, math, re, sys
from collections import Counter

def toks(s):
    return re.findall(r"[a-z0-9]+", s.lower())

def tfidf_cos(docs):
    """Return a cosine(a, b) over TF-IDF vectors with IDF fitted on docs."""
    df = Counter(t for d in docs for t in set(toks(d)))
    n = len(docs)
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
    def vec(s):
        tf = Counter(toks(s))
        return {t: c * idf.get(t, 1.0) for t, c in tf.items()}
    def cos(a, b):
        va, vb = vec(a), vec(b)
        dot = sum(w * vb.get(t, 0) for t, w in va.items())
        na = math.sqrt(sum(w * w for w in va.values()))
        nb = math.sqrt(sum(w * w for w in vb.values()))
        return dot / (na * nb) if na and nb else 0.0
    return cos

def score(pairs):
    cos = tfidf_cos([x for p in pairs for x in (p["prompt"], p["chosen"], p["rejected"])])
    judges = {
        "longer": lambda p: (len(p["chosen"]), len(p["rejected"])),
        "tfidf_to_prompt": lambda p: (cos(p["prompt"], p["chosen"]), cos(p["prompt"], p["rejected"])),
    }
    out = {}
    for name, f in judges.items():
        hit = 0.0
        for p in pairs:
            c, r = f(p)
            hit += 1.0 if c > r else 0.5 if c == r else 0.0
        out[name] = hit / len(pairs)
    return out

def _selfcheck():
    pairs = [{"prompt": "rain in paris on monday", "chosen": "paris had rain on monday, 4 mm",
              "rejected": "dry"}] * 3
    s = score(pairs)
    assert s["longer"] == 1.0 and s["tfidf_to_prompt"] == 1.0, s
    same = [{"prompt": "x y", "chosen": "a b", "rejected": "a b"}]
    assert score(same) == {"longer": 0.5, "tfidf_to_prompt": 0.5}

if __name__ == "__main__":
    _selfcheck()
    for path in sys.argv[1:]:
        pairs = [json.loads(l) for l in open(path) if l.strip()]
        s = score(pairs)
        print(f"{path}\tn={len(pairs)}\t" + "\t".join(f"{k}={v:.3f}" for k, v in s.items()))
