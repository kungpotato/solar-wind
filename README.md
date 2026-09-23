# Arc Risk Score API

Pay-per-call wallet risk-score API for autonomous agents on Arc mainnet.
`$0.01` USDC per lookup, settled by the caller broadcasting its own EIP-3009
payment on Arc — no facilitator, no signup, no API key.

**Live:** https://arc-risk-score-worker.kittisak-py-68b.workers.dev
(try `GET /health`, `GET /.well-known/x402.json`, or `GET /risk/{address}` — the last one returns `402 Payment Required` until paid)

## Proof it works

A real `$0.01` USDC payment, broadcast by the reference agent, verified by the
live deployment above, on Arc mainnet — not a testnet, not a mock:

- **Transaction:** [`0x76c16c2c2167816d77b6705c01e37a03827f93de7ee00cbf17c3f02a748364fc`](https://explorer.arc.io/tx/0x76c16c2c2167816d77b6705c01e37a03827f93de7ee00cbf17c3f02a748364fc) — anyone can open this and see the transfer independently, no need to take our word for it.
- **From (agent):** `0x80771D0E7422d458a662a61bDDad97B48a97A8fd` · **To (provider):** `0xef01a95B2a0e5076Bf5A425644afeCfE498910d7` · **Amount:** `10000` (6-decimal USDC = `$0.01`)
- **What the API returned right after**, computed live from that same address's real on-chain history — not a fixture:
  ```json
  {
    "address": "0x80771D0E7422d458a662a61bDDad97B48a97A8fd",
    "score": 70,
    "level": "low",
    "factors": {
      "isContract": false,
      "txCount": 6,
      "walletAgeDays": 0,
      "usdcTransferCount": 6,
      "sanctionsHit": false,
      "contractVerified": "unknown"
    }
  }
  ```
- Reproduce it yourself: `cd client && npm install && cp .env.example .env` (fill in a funded Arc wallet), then `npm start`.

- [`worker/`](worker/) — the resource server (Hono on Cloudflare Workers). This is the product.
- [`client/`](client/) — a reference "AI agent" script used only to prove the whole loop works end to end. Not part of the product.
- [`docs/epic-agent-pay-per-call-gateway.md`](docs/epic-agent-pay-per-call-gateway.md) — epic, user stories, acceptance criteria.
- [`docs/high-level-design-api-client.md`](docs/high-level-design-api-client.md) — API contract, client responsibilities, failure modes.
- [`docs/architecture-flow.svg`](docs/architecture-flow.svg) — payment sequence (agent → 402 → broadcast → Arc → data).
- [`docs/api-architecture.svg`](docs/api-architecture.svg) — component architecture (Hono routes, x402 middleware, risk engine).
- [`docs/epic-story-sequence.svg`](docs/epic-story-sequence.svg) — the epic end to end, stories 1-6 in order (provider → agent → Arc mainnet → agent → reviewer).
- [`docs/api-sequence-diagram.html`](docs/api-sequence-diagram.html) — UML-style sequence diagram of the actual HTTP/RPC exchange between client, API server, and Arc mainnet.

## How it works

1. Agent calls `GET /risk/{address}`.
2. Server replies `402 Payment Required` with price and payment details.
3. Agent signs and broadcasts its own EIP-3009 `transferWithAuthorization` directly to Arc mainnet — gas and payment come out of the same USDC balance, since USDC is Arc's native gas token.
4. Arc mainnet confirms the transfer.
5. Server verifies the transaction and returns the risk score.

This uses [`x402-arc`](https://github.com/kaditang/x402-arc), a community
implementation of an open, **unratified** x402-foundation proposal
([x402-foundation/x402#3504](https://github.com/x402-foundation/x402/issues/3504))
for chains where gas is the payment asset. It's the only path that works end
to end on Arc mainnet today for a plain EOA wallet — Circle's own Gateway
facilitator requires pre-depositing funds into a separate `GatewayWalletBatched`
contract, which is a different integration than plain x402.

## Bugs found and fixed while getting a real payment to go through

Both confirmed by instrumenting the deployed Worker and reproducing locally — not guessed:

- **Header name mismatch.** `x402-arc/client`'s `toPaymentHeader()` targets `X-PAYMENT`, but the installed `@x402/core` (2.13.x, via `@x402/hono`) only reads the same base64(JSON) payload from `PAYMENT-SIGNATURE`. Under `X-PAYMENT` alone, `@x402/core` silently treated every paid request as unpaid and re-issued a fresh 402 — it never even called the facilitator. Fixed by sending both headers from `client/run-reference-agent.ts`.
- **`ArcRpc` breaks under Cloudflare Workers' `fetch`.** `x402-arc`'s `ArcRpc` stores a bare reference to the global `fetch` and calls it as `this.doFetch(...)`. Workers' native `fetch` throws `"Illegal invocation"` when called detached like that; Node.js doesn't mind, which is why this only broke once deployed, not in local testing. Fixed by constructing our own `ArcRpc` with an arrow-wrapped `fetchImpl` in `worker/src/index.ts` and passing it into `ArcLocalFacilitator`.

## Known v1 limitations — stated on purpose, not hidden

- **`x402-arc@0.1.0` is new and its API may move.** `worker/src/index.ts` and `client/run-reference-agent.ts` type-check against the actual installed package (`ArcLocalFacilitator`, `ArcExactScheme`, `ARC_USDC`, `payOnArc`, `toPaymentHeader`, `readPaymentRequired`, `selectArcRequirements`) — re-run `npm run typecheck` after any `npm update` to catch a breaking release.
- **Replay protection (`MemorySpentStore`) is in-memory, per Worker isolate.** Fine for this demo's single-shot proof; Cloudflare can route to or recycle a different isolate at any time, so a real deployment needs a Durable Object or KV-backed store instead. See the comment above `ArcLocalFacilitator` in `worker/src/index.ts`.
- **Contract source verification is always reported `unknown`.** No confirmed Arc explorer verification API was found while building this — the field is honestly `unknown` rather than guessed.
- **Recent-activity window is capped at ~200k blocks.** Works today because Arc mainnet is only days old (launched 2026-09-16), so the cap still covers "since genesis." Swap for an indexer before that stops being true.
- **Sanctions watchlist ships empty.** Populate `worker/src/watchlist.json` from a real public dataset (e.g. OFAC SDN crypto addresses) before this check means anything.

## Setup

```bash
cd worker && npm install && npm test    # scoring logic, no network or funds needed
cp .env.example .dev.vars               # fill in .dev.vars, then:
npm run dev

cd ../client && npm install && cp .env.example .env     # fill in .env, then:
npm start
```
