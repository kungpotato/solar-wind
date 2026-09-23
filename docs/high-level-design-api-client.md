# High-level design: API ↔ client integration

How the Arc Risk Score resource server (`worker/`) and the reference agent
(`client/`) actually talk to each other. Diagrams: [`architecture-flow.svg`](architecture-flow.svg) (payment sequence), [`api-architecture.svg`](api-architecture.svg) (server internals).

## Components

| Component | What it is | Where |
|---|---|---|
| Resource server | Hono app on Cloudflare Workers. Owns pricing, payment verification, and the risk-scoring logic. This is the product. | `worker/src/index.ts`, `worker/src/risk.ts` |
| Client | A reference "AI agent" script. Proves the loop works; not part of what's sold. | `client/demo.ts` |
| x402-arc | Library both sides import. Server side verifies payments with no facilitator; client side signs and broadcasts them. | `worker/node_modules/x402-arc`, same in `client/` |
| Arc mainnet | Settlement layer both sides read from / write to directly via RPC. Not a component we run. | `https://rpc.mainnet.arc.io` |

There is no shared backend, database, or session between server and client —
each request is a self-contained payment-then-answer exchange. The only
persistent state on the server side is the in-memory spent-authorization
store (replay protection), scoped to one Worker isolate.

## API contract

### `GET /health`
Plain liveness check, no payment. `{ ok: true, ts: <ms> }`.

### `GET /.well-known/x402.json`
Static discovery document. Lets a generic x402-aware agent find this
resource without hard-coding it: price, network, scheme.

### `GET /risk/:address`
The paid endpoint. Two states:

**No `X-PAYMENT` header, or an invalid one** — the x402-arc middleware
short-circuits before the route handler ever runs:
```
402 Payment Required
{
  "x402Version": 2,
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:5042",
    "asset": "<ARC_USDC>",
    "amount": "10000",          // $0.01 at 6 decimals
    "payTo": "<SERVER_PAY_TO_ADDRESS>",
    "maxTimeoutSeconds": ...,
    "extra": { ... }             // challenge nonce/seed — see x402-arc
  }]
}
```

**Valid `X-PAYMENT` header** (a client-broadcast tx already confirmed on
Arc) — middleware claims the authorization, then the route handler runs:
```
200 OK
{
  "address": "0x...",
  "score": 67,
  "level": "medium",
  "factors": {
    "address": "0x...",
    "isContract": false,
    "txCount": 5,
    "walletAgeDays": 1.2,
    "usdcTransferCount": 1,
    "sanctionsHit": false,
    "contractVerified": "unknown"
  }
}
```

**Failure modes**, both surfaced as plain JSON, not thrown:
- `400 { "error": "invalid_address_or_rpc_failure" }` — bad address, or Arc RPC failed mid-lookup (`computeRiskScore` catch block in `index.ts`).
- `404 { "error": "not_found" }` — anything outside the three routes above.
- `500 { "error": "internal_error" }` — anything unhandled (`app.onError`).

## Client responsibilities

`client/demo.ts` is the whole client-side contract, in order:

1. `GET /risk/{address}` with no payment.
2. Expect `402`. Parse it with `readPaymentRequired` (handles both a JSON
   body and a base64 `payment-required` header — servers may use either).
3. `selectArcRequirements(challenge, 'mainnet')` — pick the Arc option out
   of `accepts[]` (a server could in principle offer more than one chain).
4. `payOnArc({ privateKey, requirements, chain: 'mainnet' })` — signs an
   EIP-3009 authorization **and broadcasts it itself** directly to Arc.
   This is the one non-obvious part of the contract: on most x402 chains
   the client only signs and the facilitator broadcasts; here the client
   IS the broadcaster, because Arc gas is USDC and there's no facilitator
   to hand the signed authorization to.
5. Retry the identical `GET` with `X-PAYMENT: toPaymentHeader(payment, requirements)`.
6. Expect `200`. Anything else is a hard failure — the script throws
   rather than retrying or guessing, since a silent retry on a payment
   path risks a double spend.

A real third-party agent doesn't need to look like this script at all — any
client that speaks the same three steps (call → 402 → pay → retry) works,
including generic x402 agent frameworks that support the
`eip3009-client-broadcast` asset transfer method.

## Non-functional notes

- **Price is fixed and single-scheme**: `$0.01`, `exact`, `eip155:5042` only. No tiers, no negotiation.
- **Idempotency**: a given signed authorization can only be claimed once (`ArcLocalFacilitator`, `claimOn: 'verify'`). Two identical requests in flight can race; the loser gets rejected, not double-charged.
- **Replay store is per-isolate memory** — see the limitation already tracked in [`../README.md`](../README.md#known-v1-limitations--stated-on-purpose-not-hidden). It does not survive Cloudflare recycling or routing to a different isolate.
- **No auth, no API key, no session** — the payment itself is the only credential. Anyone who can pay can call.
- **Timeouts**: bounded by `maxTimeoutSeconds` in the payment requirements and by however long `computeRiskScore`'s bounded RPC calls take (worst case: one binary search + two `getLogs` calls over the capped block window).

## Out of scope for this design

- Multiple priced resources or tiered pricing (one endpoint, one price today).
- A persistent/shared replay store (Durable Object or KV) — noted as a v1 gap, not built.
- Contract source verification (`contractVerified` is honestly `unknown` — no wired-up data source yet).
