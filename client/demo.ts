// Reference agent for the Arc Risk Score API.
//
// This is the "AI agent" box in the architecture diagram, kept intentionally
// small: call the endpoint, read the 402, pay for real, call it again. It
// exists to prove the whole loop works end to end on Arc mainnet — it is
// not part of the product being sold.
import 'dotenv/config'
import { payOnArc, toPaymentHeader } from 'x402-arc/client'
import { readPaymentRequired, selectArcRequirements } from 'x402-arc'

const PRIVATE_KEY = requireEnv('AGENT_PRIVATE_KEY') as `0x${string}`
const API_URL = requireEnv('API_URL')
const TARGET_ADDRESS = requireEnv('TARGET_ADDRESS')

function requireEnv(name: string): string {
  const value = process.env[name]
  if (!value) throw new Error(`Missing required env var: ${name}`)
  return value
}

async function main() {
  const url = `${API_URL}/risk/${TARGET_ADDRESS}`

  console.log(`$ GET ${url}`)
  const firstTry = await fetch(url)

  if (firstTry.status !== 402) {
    throw new Error(`Expected 402 Payment Required on the unpaid call, got ${firstTry.status}`)
  }

  const challenge = await readPaymentRequired(firstTry)
  const requirements = challenge && selectArcRequirements(challenge, 'mainnet')
  if (!requirements) {
    throw new Error('Server did not offer an Arc (eip155:5042) payment option')
  }
  console.log('402 Payment Required ·', JSON.stringify(requirements))

  console.log('signing & broadcasting EIP-3009 payment on Arc mainnet...')
  const payment = await payOnArc({
    privateKey: PRIVATE_KEY,
    requirements,
    chain: 'mainnet',
  })
  console.log('settled · tx', payment.transaction)

  const paidTry = await fetch(url, {
    headers: { 'X-PAYMENT': toPaymentHeader(payment, requirements) },
  })

  if (!paidTry.ok) {
    throw new Error(`Paid call failed: ${paidTry.status} ${await paidTry.text()}`)
  }

  const result = await paidTry.json()
  console.log('200 OK ·', JSON.stringify(result, null, 2))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
