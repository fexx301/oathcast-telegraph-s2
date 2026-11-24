# Reproduce the OathCast evaluation work (beginner tutorial)

This walks through checking our Telegraph Season II Evaluators work yourself. **No wallet is needed:** every step is
free and uses public, keyless data. It takes about 20 minutes.

Disclosure: this is a hackathon entry. I'm competing in Telegraph Hackathon Season II, which has prizes.

## Words used here, in plain English

- **Telegraph:** a network that sells answers. An app pays a little per question, and a **miner** (a service that
  answers one kind of question, called an **Intent**) replies.
- **Evaluator:** something that judges whether miners' answers are right, so the network can rank them. That's what
  this repo is about.
- **Truth source:** a public, trusted place to look up the correct answer (for example, a weather station's record).
- **Comparator:** a tiny program that decides whether a miner's number is close enough to the true number.
- **Adapter:** a small trained add-on to Telegraph's shared AI model. It reads two answers to the same question and
  scores which one is better.
- **Preference pair:** one question with a better and a worse answer, used to train and test adapters.
- **Canonical:** the scorer the network currently uses for an Intent. A new one replaces it only by doing better on
  hidden test pairs.
- **Diamond:** Telegraph's main smart contract on the Ethereum Sepolia test network, where registrations are recorded.
- **Hash (sha256, keccak256):** a fingerprint of a file. The same file always gives the same fingerprint, so you can
  check that what's published is exactly what was registered.

## What you need

- A terminal with `curl` and Python 3 (standard library is enough for steps 1, 3 and 4).
- [`uv`](https://docs.astral.sh/uv/) for step 2 (it installs `wasmtime` on the fly), and for the keccak check in
  step 4 (it installs `pycryptodome` on the fly).
- [Foundry](https://getfoundry.sh) (`cast`) only for step 5.
- This repo: `git clone https://github.com/fexx301/oathcast-telegraph-s2 && cd oathcast-telegraph-s2`

## Network and costs (for context; none of this is needed to reproduce)

- **Network:** Telegraph runs on **Ethereum Sepolia** (testnet). Since **17 Nov 2026** the contract (the "Diamond")
  is `0x72a70e949362670Bf8bceAd24eFC5b8f950aa08b`. It replaced `0x3624…b99b`, which is retired.
- **Uploading evaluation material** is a signed request, with no gas and no bond.
- **Registering a scoring module** (an adapter or a comparator) takes a bond, now **5 test USDC** on the new
  Diamond (read it with `entityBonds()`; anyone can mint test USDC), plus a little Sepolia ETH for gas. Our
  registrations in this repo were made on the old Diamond, where the bond was paid in MACHINA.

## 1. Call the truth sources

Truth sources are the public reference answers an evaluator checks miners against. Ours need no key:

```sh
# Weather (WEATHER_FORECAST_VERIFY): the nearest NOAA GHCN-Daily station's record for a place and day
curl -s 'https://wdauaeyvk7mcfzuxewk3mqkhvu0klqwo.lambda-url.eu-north-1.on.aws/verify?location=Denver,%20Colorado&date=2026-10-20'
# -> "temp_max_c": 21.1 at station USC00052223 (DENVER WATER DEPT, 2.3 km away), with the NOAA query URL it used

# Sanctions (SANCTIONS_SCREENING_MATCH): OFAC SDN and non-SDN, UN and EU lists, rebuilt daily
curl -s 'https://ngrgakvwtxioa2kkdllvhn5pza0fxqcb.lambda-url.eu-north-1.on.aws/screen?name=Lazarus%20Group'
# -> "matched": true, "LAZARUS GROUP" on OFAC SDN, score 1.00, plus each list's publication date

# SSL (SSL_VERIFICATION_CERT): a live TLS handshake with hostname verification; private addresses refused
curl -s 'https://rxmhjv4nbzdeshevacrsvteaqy0csphi.lambda-url.eu-north-1.on.aws/check?host=expired.badssl.com'
# -> "valid": false, "reason": "certificate rejected: certificate has expired"

# Macro (MACRO_ECONOMIC_INDICATOR): the World Bank WDI API, called directly (no wrapper of ours)
curl -s 'https://api.worldbank.org/v2/country/USA/indicator/SL.UEM.TOTL.ZS?date=2019&format=json'
# -> "value": 3.669 (US unemployment, 2019, modelled ILO estimate)
```

What each source does and its measured accuracy are in [wfv-station-source-v1](wfv-station-source-v1/),
[sanctions-truth-source-v1](sanctions-truth-source-v1/), [ssl-truth-source-v1](ssl-truth-source-v1/) and
[macro-truth-source-v1](macro-truth-source-v1/).

## 2. Run the comparator test

The comparator decides how close a miner's number must be to the reference to count. It's a 2.5 KB WASM module with
no imports.

```sh
cd macro-comparator-v1
sh oracle/fetch_zkasuran.sh       # a third-party comparator used for cross-checking, fetched rather than redistributed
uv run --no-project --with wasmtime python -I test_comparator.py macro_comparator.wasm
cd ..
```

Expected, ending in `ok`:
- the kit's reference matched on all 17,680 grid vectors and 20,000 node-shaped cases;
- 0 mismatches against the canonical CRYPTO_PRICE comparator in its domain;
- bit-identical results over 38,456 repeat and reversed runs;
- `bytes 2527`.

## 3. Run the shortcut judges on any preference pairs

A shortcut judge picks an answer with a cheap rule (the longer one; the one sharing more words with the question).
If it scores far above 50% on a set of pairs, the set can be passed without the skill it's meant to test.

```sh
python3 shortcut-judges-v1/judges.py examples/example-pairs.jsonl
# -> examples/example-pairs.jsonl  n=2  longer=1.000  tfidf_to_prompt=0.500
```

`examples/example-pairs.jsonl` holds two pairs we built for our demo video from the real Denver record in step 1.
They aren't pool rows. Two pairs are far too few to judge anything; they only show the format (`prompt`, `chosen`,
`rejected`). Run it on your own file. On our uploaded weather pairs the results were: "pick the longer" 0.497 overall
but 0.17–0.88 within error families, and prompt overlap 0.783, mostly legitimate (see
[shortcut-judges-v1/RESULT.md](shortcut-judges-v1/RESULT.md)). To split by family:
`python3 shortcut-judges-v1/by_family.py your_pairs.jsonl your_meta.jsonl family`.

## 4. Verify the weather adapter package

Our v6 adapter became the first canonical scorer for WEATHER_FORECAST_VERIFY. The bytes registered on-chain are in
[wfv-adapter-v6](wfv-adapter-v6/):

```sh
shasum -a 256 wfv-adapter-v6/WEATHER_FORECAST_VERIFY.safetensors
# -> 6d84f0dbb7181e01b894d08b5d38a05ab4301224c5863f85d608773654bcf285
uv run --no-project --with pycryptodome python -I -c "from Crypto.Hash import keccak; h=keccak.new(digest_bits=256); h.update(open('wfv-adapter-v6/WEATHER_FORECAST_VERIFY.safetensors','rb').read()); print('0x'+h.hexdigest())"
# -> 0x7cbd03343edc870036c9a23acf9fe47ebf1dccbdd25f5130f81451098e90554d (the keccak256 registered on-chain)
```

Running the adapter itself needs Telegraph's kit and foundation model (about 600 MB); see
[telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline).

## 5. Check the first-canonical record

The node was reset around 16–17 Nov 2026 and no longer lists pre-reset registrations, so there are two ways to check:

- **On-chain (permanent):** the registration transaction, `0x651122c1c392f969e6bd8726b9df09acdcf91188b5fdfd434ddc3a454eef4ef8`, on the retired Diamond:
  ```sh
  cast tx 0x651122c1c392f969e6bd8726b9df09acdcf91188b5fdfd434ddc3a454eef4ef8 --rpc-url https://ethereum-sepolia-rpc.publicnode.com
  # from 0xe9d1…dc70a to the old Diamond 0x3624…b99b, block 12128085. Its input carries the package hash from step 4:
  cast tx 0x651122c1c392f969e6bd8726b9df09acdcf91188b5fdfd434ddc3a454eef4ef8 input --rpc-url https://ethereum-sepolia-rpc.publicnode.com | grep -c 7cbd03343edc870036c9a23acf9fe47ebf1dccbdd25f5130f81451098e90554d
  # -> 1
  ```
- **The node's own record, saved before the reset:** [evidence/wfv-registry-2026-11-15.json](evidence/wfv-registry-2026-11-15.json).
  - **Reg 408 (ours):** `"decision": "first_canonical"`, "first Canonical for WEATHER_FORECAST_VERIFY at 70.00% on 30
    pairs".
  - **Reg 445 (another team):** "won … at 70.00% vs incumbent 408 at 66.67% (margin 2.00 points)".

## Limits

- **Weather station data** lags 2–8 weeks outside the US and Canada.
- **The sanctions lists** are a daily snapshot. UK lists aren't covered, and a name match is an alert that needs
  identity review, not a verdict.
- **The weather adapter** was about 70% accurate on hidden pairs (85/120 over four rounds), at the floor, which is
  why a challenger could replace it. On our own test, v6 picks the wrong answer on one of the two example pairs (the
  wrong-day one).
- **Our evaluation material** (preference pairs) isn't published, because part of the pool is a hidden test set.
  Only aggregate checks are here.
- **The macro comparator** isn't a live scorer. Telegraph uses one shared comparator for deterministic checks, so
  community comparators aren't registered (the team, 22 Nov). Step 2 checks the WASM itself against the kit's
  reference, which still holds.
