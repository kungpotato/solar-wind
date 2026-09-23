# Submission description — Arc Microgrants

Ready-to-paste text for the DoraHacks submission form's "short description
of what your project does and what it uses Arc for." Two lengths, pick
whichever fits the field's character limit.

## Short (~200 characters)

> Pay-per-call wallet risk-score API for AI agents on Arc mainnet. Agents pay $0.01 USDC per lookup by broadcasting their own EIP-3009 payment directly — no facilitator, possible only because Arc uses USDC as its native gas token.

## Full (~480 characters)

> Arc Risk Score API lets AI agents check a wallet's on-chain risk before sending it money — wallet age, transaction activity, USDC engagement, contract status, and sanctions screening, all computed live from real Arc RPC data, never mocked. Priced at $0.01 USDC per lookup, agents pay by signing and broadcasting their own EIP-3009 authorization directly on Arc mainnet, with no facilitator in the loop — a settlement pattern possible only because Arc uses USDC as its native gas token. Fully deployed, verified with a real on-chain payment, and open source.

## Why these two lead with the Arc angle first

Per the grant page, reviewers weigh "relevance to Arc" and "technical
credibility" first — both descriptions put the Arc-specific mechanism
(USDC-as-gas, no facilitator, client-broadcast EIP-3009) in the first
sentence rather than burying it, so a skim-reader still gets it.
