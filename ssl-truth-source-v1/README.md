# SSL_VERIFICATION_CERT truth source v1 (2026-11-23)

**Why:** SSL_VERIFICATION_CERT is a deterministic Intent on the generic scorer. Its pool had 3 submitters but only
**2 of the 3 eligible** it needs (intent scan v2, 22 Nov). Ahmed asked for truth sources where they're missing.

**What the node expects** (`/engine/v1/intents/SSL_VERIFICATION_CERT`): comparator code 3, tolerance 0, scale 1, a
pass/fail answer per host. Questions follow "Is the TLS certificate of {key} currently valid and trusted?", over
`google.com`, `github.com`, `expired.badssl.com` and `self-signed.badssl.com`.

**The source:** `GET /check?host=` on `https://rxmhjv4nbzdeshevacrsvteaqy0csphi.lambda-url.eu-north-1.on.aws`. It's
keyless (AWS Lambda `telegraph-ssl-check`, eu-north-1, OathCast account; `aws/deploy.sh` refuses any other account).
- **The check:** a real TLS handshake on port 443 with hostname verification against a pinned trust store (Mozilla's
  root list via certifi).
- **Returns:** `valid`, the reason, the expiry date, days remaining, the issuer and the DNS names.
- **Refuses:** hosts that resolve to private, loopback, link-local or reserved addresses.

**Tested** (`test_check.py`, live, 23 Nov): 11/11.
- **Valid:** google.com, github.com, badssl.com.
- **Rejected:** expired, self-signed, wrong-host and untrusted-root certificates (badssl.com).
- **Refused:** localhost, raw IPs, an internal name, and a public name that resolves to the metadata address.
- **The deployed endpoint** answers the node's four hosts correctly.

**Limits:**
- revocation (OCSP/CRL) isn't checked, so a revoked certificate that is otherwise valid reads as valid;
- the trust store is Mozilla's, not any one operating system's;
- one handshake from one region (eu-north-1).

**Outcome:** uploaded in Anjoman on 23 Nov (`items.jsonl`, `label_kind: truth_source`) and admitted. After the epoch
rollover our row was **eligible** and the pool became **evaluable**: 3 of 3 eligible contributors, snapshot published
2026-11-23 01:08 UTC (activation epoch 41).
