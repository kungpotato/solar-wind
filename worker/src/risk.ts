import { type PublicClient, parseAbiItem, isAddressEqual, getAddress } from 'viem'
import watchlist from './watchlist.json'

const TRANSFER_EVENT = parseAbiItem(
  'event Transfer(address indexed from, address indexed to, uint256 value)'
)

// Arc mainnet is only days old at the time this was written, so a bounded
// recent-block window still covers "since genesis" for now. This does NOT
// scale as the chain grows — swap for an indexer/subgraph before that stops
// being true. Tracked as a known v1 limitation, not hidden.
const MAX_LOOKBACK_BLOCKS = 200_000n

export type RiskFactors = {
  address: string
  isContract: boolean
  txCount: number
  walletAgeDays: number | null
  usdcTransferCount: number
  sanctionsHit: boolean
  contractVerified: 'yes' | 'no' | 'unknown'
}

export type RiskResult = {
  address: string
  score: number
  level: 'low' | 'medium' | 'high'
  factors: RiskFactors
}

export async function findFirstSeenBlock(
  client: PublicClient,
  address: `0x${string}`,
  latestBlock: bigint
): Promise<bigint | null> {
  const nonceAtLatest = await client.getTransactionCount({ address, blockNumber: latestBlock })
  if (nonceAtLatest === 0) return null

  let low = 0n
  let high = latestBlock
  while (low < high) {
    const mid = low + (high - low) / 2n
    const nonce = await client.getTransactionCount({ address, blockNumber: mid })
    if (nonce > 0) {
      high = mid
    } else {
      low = mid + 1n
    }
  }
  return low
}

async function getUsdcTransferCount(
  client: PublicClient,
  address: `0x${string}`,
  usdcAddress: `0x${string}`,
  fromBlock: bigint,
  toBlock: bigint
): Promise<number> {
  const [outgoing, incoming] = await Promise.all([
    client.getLogs({
      address: usdcAddress,
      event: TRANSFER_EVENT,
      args: { from: address },
      fromBlock,
      toBlock,
    }),
    client.getLogs({
      address: usdcAddress,
      event: TRANSFER_EVENT,
      args: { to: address },
      fromBlock,
      toBlock,
    }),
  ])
  const uniqueTxHashes = new Set([...outgoing, ...incoming].map((log) => log.transactionHash))
  return uniqueTxHashes.size
}

export function checkWatchlist(
  address: string,
  addresses: string[] = watchlist.addresses as string[]
): boolean {
  const target = address.toLowerCase()
  return addresses.some((a) => a.toLowerCase() === target)
}

export function scoreFactors(f: RiskFactors): { score: number; level: 'low' | 'medium' | 'high' } {
  if (f.sanctionsHit) {
    // Hard override — a sanctions hit is a block, not a point deduction.
    return { score: 5, level: 'high' }
  }

  let score = 0

  // Tx activity depth, 0-30
  if (f.txCount >= 20) score += 30
  else if (f.txCount >= 5) score += 20
  else if (f.txCount >= 1) score += 10

  // USDC engagement, 0-25
  if (f.usdcTransferCount >= 5) score += 25
  else if (f.usdcTransferCount >= 1) score += 15

  // Wallet age, 0-20 (bounded by how young Arc mainnet itself is)
  if (f.walletAgeDays !== null) {
    if (f.walletAgeDays >= 3) score += 20
    else if (f.walletAgeDays >= 1) score += 12
    else score += 5
  }

  // Contract check, 0-15
  if (!f.isContract) score += 10
  else if (f.contractVerified === 'yes') score += 15
  else if (f.contractVerified === 'unknown') score += 5

  // Clean sanctions screen, +10
  score += 10

  score = Math.min(100, score)
  const level = score >= 70 ? 'low' : score >= 40 ? 'medium' : 'high'
  return { score, level }
}

export async function computeRiskScore(
  client: PublicClient,
  rawAddress: string,
  usdcAddress: `0x${string}`
): Promise<RiskResult> {
  const address = getAddress(rawAddress)
  const latestBlock = await client.getBlockNumber()

  const [bytecode, txCount, firstSeenBlock] = await Promise.all([
    client.getBytecode({ address }),
    client.getTransactionCount({ address }),
    findFirstSeenBlock(client, address, latestBlock),
  ])

  let walletAgeDays: number | null = null
  if (firstSeenBlock !== null) {
    const firstBlock = await client.getBlock({ blockNumber: firstSeenBlock })
    walletAgeDays = (Date.now() / 1000 - Number(firstBlock.timestamp)) / 86400
  }

  const fromBlock =
    firstSeenBlock !== null && latestBlock - firstSeenBlock <= MAX_LOOKBACK_BLOCKS
      ? firstSeenBlock
      : latestBlock > MAX_LOOKBACK_BLOCKS
        ? latestBlock - MAX_LOOKBACK_BLOCKS
        : 0n

  const usdcTransferCount = await getUsdcTransferCount(
    client,
    address,
    usdcAddress,
    fromBlock,
    latestBlock
  )

  const factors: RiskFactors = {
    address,
    isContract: !!bytecode && bytecode !== '0x',
    txCount,
    walletAgeDays: walletAgeDays === null ? null : Math.round(walletAgeDays * 10) / 10,
    usdcTransferCount,
    sanctionsHit: checkWatchlist(address),
    // No confirmed Arc explorer verification API at the time this was written.
    // Wire this up to that API when it's available; until then every
    // contract is honestly reported as unverified rather than guessed.
    contractVerified: 'unknown',
  }

  const { score, level } = scoreFactors(factors)
  return { address, score, level, factors }
}
