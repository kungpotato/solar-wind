import { Hono } from 'hono'
import { paymentMiddleware, x402ResourceServer } from '@x402/hono'
import { ArcLocalFacilitator, ArcExactScheme, ARC_USDC } from 'x402-arc'
import { createPublicClient, http, type Hex } from 'viem'
import { computeRiskScore } from './risk'

type Env = {
  SERVER_PAY_TO_ADDRESS: string
  ARC_RPC_URL: string
}

const ARC_CHAIN = {
  id: 5042,
  name: 'Arc',
  nativeCurrency: { name: 'USDC', symbol: 'USDC', decimals: 18 },
  rpcUrls: { default: { http: ['https://rpc.mainnet.arc.io'] } },
} as const

const PRICE = '$0.01'

const app = new Hono<{ Bindings: Env }>()

app.onError((err, c) => {
  console.error('unhandled', err)
  return c.json({ error: 'internal_error' }, 500)
})

app.notFound((c) => c.json({ error: 'not_found' }, 404))

app.get('/health', (c) => c.json({ ok: true, ts: Date.now() }))

app.get('/.well-known/x402.json', (c) =>
  c.json({
    x402Version: 2,
    lastUpdated: new Date().toISOString(),
    accepts: [{ scheme: 'exact', network: 'eip155:5042', price: PRICE }],
    metadata: {
      name: 'Arc Risk Score API',
      description:
        'Wallet risk score for any address on Arc mainnet, computed from on-chain activity. $0.01 USDC per lookup, settled by the caller broadcasting its own EIP-3009 payment (no facilitator).',
    },
  })
)

// Stateful, so build once per isolate rather than per request.
let cachedMiddleware: ReturnType<typeof paymentMiddleware> | undefined
function paidRouteMiddleware(env: Env) {
  if (cachedMiddleware) return cachedMiddleware
  // "Local" facilitator = runs in this same isolate, not a remote service —
  // there's no third party to sponsor gas here, so its only job is checking
  // the client's already-broadcast tx against Arc RPC.
  //
  // claimOn defaults to 'verify' (not 'settle') on purpose: @x402/core
  // settles AFTER the handler runs, so claiming on settle lets a replayed
  // payment execute the handler once for free before being rejected. Keep
  // the default — see x402-arc's facilitator.ts for the measured bug this
  // avoids.
  //
  // MemorySpentStore (the default) is per-isolate and does not survive
  // Cloudflare recycling an isolate or routing to a different one. Fine for
  // this demo's single-shot proof; replace with a Durable Object or KV
  // before relying on replay protection at real traffic.
  const facilitator = new ArcLocalFacilitator({ chain: 'mainnet', rpcUrl: env.ARC_RPC_URL })
  const server = new x402ResourceServer(facilitator).register(
    'eip155:5042',
    new ArcExactScheme({ chain: 'mainnet' })
  )
  cachedMiddleware = paymentMiddleware(
    {
      'GET /risk/:address': {
        accepts: {
          scheme: 'exact',
          network: 'eip155:5042',
          price: PRICE,
          payTo: env.SERVER_PAY_TO_ADDRESS,
        },
        description: 'Wallet risk score for one Arc address.',
      },
    },
    server
  )
  return cachedMiddleware
}

app.use('/risk/:address', (c, next) => paidRouteMiddleware(c.env)(c, next))

app.get('/risk/:address', async (c) => {
  const address = c.req.param('address')
  const client = createPublicClient({ chain: ARC_CHAIN, transport: http(c.env.ARC_RPC_URL) })
  try {
    const result = await computeRiskScore(client, address, ARC_USDC as Hex)
    return c.json(result)
  } catch (err) {
    console.error('risk_score_failed', err)
    return c.json({ error: 'invalid_address_or_rpc_failure' }, 400)
  }
})

export default app
