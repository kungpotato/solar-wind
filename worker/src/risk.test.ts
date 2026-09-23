import { describe, expect, it } from 'vitest'
import type { PublicClient } from 'viem'
import {
  checkWatchlist,
  computeRiskScore,
  findFirstSeenBlock,
  scoreFactors,
  type RiskFactors,
} from './risk'

const ADDRESS = '0x1234567890123456789012345678901234567890'
const USDC = '0xAaAAaaAaaAaaAaaAaAAAAAAAAAaaaAAAaaaaAAaA'

function baseFactors(overrides: Partial<RiskFactors> = {}): RiskFactors {
  return {
    address: ADDRESS,
    isContract: false,
    txCount: 0,
    walletAgeDays: null,
    usdcTransferCount: 0,
    sanctionsHit: false,
    contractVerified: 'unknown',
    ...overrides,
  }
}

describe('scoreFactors', () => {
  it('overrides everything to a fixed low score on a sanctions hit', () => {
    const result = scoreFactors(
      baseFactors({ sanctionsHit: true, txCount: 999, usdcTransferCount: 999, walletAgeDays: 30 })
    )
    expect(result).toEqual({ score: 5, level: 'high' })
  })

  it('scores a brand-new, never-used EOA as high risk', () => {
    const result = scoreFactors(baseFactors())
    // 0 (activity) + 0 (usdc) + 0 (age unknown) + 10 (EOA) + 10 (clean) = 20
    expect(result.score).toBe(20)
    expect(result.level).toBe('high')
  })

  it('scores an established, active EOA as low risk', () => {
    const result = scoreFactors(
      baseFactors({ txCount: 25, usdcTransferCount: 8, walletAgeDays: 5, isContract: false })
    )
    // 30 (activity) + 25 (usdc) + 20 (age) + 10 (EOA) + 10 (clean) = 95
    expect(result.score).toBe(95)
    expect(result.level).toBe('low')
  })

  it('lands in the medium band at the documented boundary', () => {
    const result = scoreFactors(
      baseFactors({ txCount: 5, usdcTransferCount: 1, walletAgeDays: 1, isContract: false })
    )
    // 20 + 15 + 12 + 10 + 10 = 67
    expect(result.score).toBe(67)
    expect(result.level).toBe('medium')
  })

  it('gives an unverified contract fewer points than a plain EOA', () => {
    const eoa = scoreFactors(baseFactors({ isContract: false }))
    const unverifiedContract = scoreFactors(
      baseFactors({ isContract: true, contractVerified: 'unknown' })
    )
    expect(unverifiedContract.score).toBeLessThan(eoa.score)
  })
})

describe('checkWatchlist', () => {
  it('is false when the address is not on the list', () => {
    expect(checkWatchlist(ADDRESS, ['0xdead...'])).toBe(false)
  })

  it('matches case-insensitively', () => {
    expect(checkWatchlist(ADDRESS.toUpperCase(), [ADDRESS.toLowerCase()])).toBe(true)
  })

  it('defaults to the empty starter list shipped in watchlist.json', () => {
    expect(checkWatchlist(ADDRESS)).toBe(false)
  })
})

describe('findFirstSeenBlock', () => {
  function fakeClientWithNonceAt(nonceByBlock: (block: bigint) => number) {
    return {
      getTransactionCount: async ({ blockNumber }: { blockNumber: bigint }) =>
        nonceByBlock(blockNumber),
    } as unknown as PublicClient
  }

  it('returns null for a wallet that has never sent a transaction', async () => {
    const client = fakeClientWithNonceAt(() => 0)
    const result = await findFirstSeenBlock(client, ADDRESS, 1000n)
    expect(result).toBeNull()
  })

  it('binary-searches to the exact first block with nonce > 0', async () => {
    const firstActiveBlock = 777n
    const client = fakeClientWithNonceAt((block) => (block >= firstActiveBlock ? 1 : 0))
    const result = await findFirstSeenBlock(client, ADDRESS, 1000n)
    expect(result).toBe(firstActiveBlock)
  })

  it('handles a wallet active since block 0', async () => {
    const client = fakeClientWithNonceAt(() => 1)
    const result = await findFirstSeenBlock(client, ADDRESS, 1000n)
    expect(result).toBe(0n)
  })
})

describe('computeRiskScore', () => {
  it('wires a fresh, unused wallet through to a high-risk result', async () => {
    const client = {
      getBlockNumber: async () => 1000n,
      getBytecode: async () => '0x',
      getTransactionCount: async () => 0,
      getBlock: async () => ({ timestamp: BigInt(Math.floor(Date.now() / 1000)) }),
      getLogs: async () => [],
    } as unknown as PublicClient

    const result = await computeRiskScore(client, ADDRESS, USDC)

    expect(result.address).toBe(ADDRESS)
    expect(result.factors.isContract).toBe(false)
    expect(result.factors.txCount).toBe(0)
    expect(result.factors.walletAgeDays).toBeNull()
    expect(result.factors.contractVerified).toBe('unknown')
    expect(result.level).toBe('high')
  })
})
