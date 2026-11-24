"""Live checks against public test hosts (badssl.com publishes certificates that are deliberately broken)."""
import json, sys
sys.path.insert(0, "app")
import lambda_function as L

CASES = {"google.com": True, "github.com": True, "expired.badssl.com": False, "self-signed.badssl.com": False,
         "wrong.host.badssl.com": False, "untrusted-root.badssl.com": False, "badssl.com": True}
ok = True
for host, want in CASES.items():
    r = L.check(host)
    good = r["valid"] is want
    ok &= good
    print(("ok  " if good else "FAIL"), host, r["valid"], "|", r["reason"])
for bad in ("localhost", "127.0.0.1", "metadata.google.internal", "169.254.169.254.nip.io"):
    h = L.clean_host(bad)
    r = L.check(h) if h else {"valid": False, "reason": "rejected as not a hostname"}
    good = r["valid"] is False
    ok &= good
    print(("ok  " if good else "FAIL"), "refuse", bad, "|", r["reason"])
assert L.clean_host("Is the TLS certificate of GitHub.com currently valid and trusted?") == "github.com"
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
