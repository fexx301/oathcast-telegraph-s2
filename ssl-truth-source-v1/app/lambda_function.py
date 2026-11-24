"""SSL_VERIFICATION_CERT truth source: is a hostname's TLS certificate currently valid and trusted?

GET /check?host=example.com -> {"host", "valid", "reason", "not_after", "days_remaining", "issuer", "subject_alt_names",
"trust_store", "checked_at"}. A real TLS handshake on port 443 with hostname verification against a pinned trust store
(Mozilla's root list via certifi). Keyless. Revocation (OCSP/CRL) is not checked: a revoked but otherwise valid
certificate reads as valid, and that limit is stated in the answer.
Only public addresses are dialled: hosts resolving to private, loopback, link-local or reserved addresses are refused."""
import ipaddress, json, re, socket, ssl
from datetime import datetime, timezone

import certifi

HOST = re.compile(r"^(?=.{1,253}$)(?!-)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")
CTX = ssl.create_default_context(cafile=certifi.where())
STORE = f"Mozilla root list via certifi {certifi.__version__}"


def clean_host(raw):
    """Accept a bare hostname or one embedded in a URL or question; return the lowercase hostname or None."""
    s = (raw or "").strip().lower()
    m = re.search(r"(?:https?://)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,63})", s)
    h = m.group(1).rstrip(".") if m else ""
    return h if HOST.match(h) else None


def public_ip(host):
    """The first resolved address, only if every address the name resolves to is public."""
    infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addrs = [i[4][0] for i in infos]
    if not addrs or any(not ipaddress.ip_address(a).is_global for a in addrs):
        return None
    return addrs[0]


def check(host, now=None):
    now = now or datetime.now(timezone.utc)
    out = {"host": host, "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "trust_store": STORE,
           "revocation_checked": False}
    try:
        ip = public_ip(host)
    except socket.gaierror:
        return {**out, "valid": False, "reason": "host does not resolve"}
    if ip is None:
        return {**out, "valid": False, "reason": "refused: the host resolves to a non-public address"}
    try:
        with socket.create_connection((ip, 443), timeout=6) as sock:
            with CTX.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
    except ssl.SSLCertVerificationError as e:
        return {**out, "valid": False, "reason": f"certificate rejected: {e.verify_message}"}
    except (ssl.SSLError, OSError) as e:
        return {**out, "valid": False, "reason": f"no TLS handshake on port 443: {type(e).__name__}"}
    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    issuer = dict(x[0] for x in cert.get("issuer", ()))
    return {**out, "valid": True, "reason": "certificate valid, trusted and matches the hostname",
            "not_after": not_after.strftime("%Y-%m-%dT%H:%M:%SZ"), "days_remaining": (not_after - now).days,
            "issuer": issuer.get("organizationName") or issuer.get("commonName"),
            "subject_alt_names": [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"][:10]}


def handler(event, context):
    path = event.get("rawPath", "/")
    q = event.get("queryStringParameters") or {}
    if path != "/check":
        return {"statusCode": 404, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "GET /check?host="})}
    host = clean_host(q.get("host") or q.get("domain") or q.get("question") or "")
    if not host:
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"error": "give a hostname, e.g. ?host=example.com"})}
    return {"statusCode": 200, "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"}, "body": json.dumps(check(host))}
