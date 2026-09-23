# Risk scoring methodology

How `GET /risk/{address}` turns one Arc address into a `0-100` score. Source
of truth: [`worker/src/risk.ts`](../worker/src/risk.ts) — this doc describes
what that file does and why; if the two disagree, the code wins.

## Design rule: every factor is either RPC-verifiable or honestly `unknown`

No factor is guessed, hardcoded, or randomized. Two of the five signals
(`txCount`, `walletAgeDays`) come from a full scan of Arc's transaction
history for that address — feasible **today** only because Arc mainnet is
just days old (launched 2026-09-16); this is a stated v1 limitation, not a
permanent design (see the README). Where no real data source exists yet
(`contractVerified`), the API says `"unknown"` rather than inventing an
answer — see [Story 6](epic-agent-pay-per-call-gateway.md#story-6--the-risk-score-must-be-computed-from-real-on-chain-data-never-mocked)
in the epic.

## The five factors and their weights

| Factor | Points | How it's computed |
|---|---|---|
| Tx activity depth | 0-30 | `txCount` from `eth_getTransactionCount` (the address's nonce) |
| USDC engagement | 0-25 | `usdcTransferCount`, unique txs found via `eth_getLogs` on the USDC contract, both directions |
| Wallet age | 0-20 | `walletAgeDays`, from binary-searching for the first block where the nonce goes from 0 to 1 |
| Contract check | 0-15 | EOA vs. contract via `eth_getCode`; contracts get a lower score than a plain EOA until source verification is wired up |
| Clean sanctions screen | +10 flat | see the hard override below — this points is really "nothing bad found" |

### Tx activity depth (0-30)
- `txCount >= 20` → 30
- `txCount >= 5` → 20
- `txCount >= 1` → 10
- `txCount == 0` → 0

### USDC engagement (0-25)
- `usdcTransferCount >= 5` → 25
- `usdcTransferCount >= 1` → 15
- `usdcTransferCount == 0` → 0

Arc's native gas token *is* USDC, so a wallet that's never touched it is a
real signal, not a technicality.

### Wallet age (0-20)
- Never active (`walletAgeDays === null`) → 0
- `< 1 day` → 5
- `1-3 days` → 12
- `>= 3 days` → 20

These thresholds are deliberately small — Arc mainnet itself is only about a
week old at the time of writing, so "3+ days" already means "here since
close to genesis." Revisit the bands as the chain matures.

### Contract check (0-15)
- Plain EOA (not a contract) → 10
- Contract, source verified → 15 *(not reachable yet — no verification data source is wired up, see below)*
- Contract, verification `unknown` → 5

### Sanctions screen — hard override, not a point deduction
A hit on `worker/src/watchlist.json` **overrides everything else**: the
result is a fixed `score: 5, level: "high"` regardless of how clean the
other four factors are. Real compliance systems block on a sanctions hit
rather than average it into a composite score, and this API does the same.
The list ships empty in v1 — see the README's known limitations.

## Turning the score into a level

```
score >= 70  → "low"
score >= 40  → "medium"
else         → "high"
```

Maximum achievable score for a clean EOA today is 95 (30+25+20+10+10) — 100
is only reachable once contract source verification is wired up, since an
unverified contract is capped at 5 points on that factor instead of 15.

## What this is not

- Not a credit score, not a guarantee, not a substitute for a real KYT/AML
  provider. It's a cheap, fast, honest signal an autonomous agent can act on
  before sending funds — nothing more.
- Not final. The weights above are a defensible v1, not a tuned model —
  there's no labeled dataset to tune against yet, because Arc mainnet barely
  has any history to learn from.
