# Epic: Automatic pay-per-call service for AI agents on Arc

**Product: Arc wallet risk score API** — an agent pays USDC per call to check a risk score for an Arc address before sending it funds (wallet age, tx activity, USDC activity, contract check, sanctions screen). Returns a 0-100 score with a breakdown of each factor — every factor is computed from real Arc RPC data, no mocked values (details: [`README.md`](../README.md), [`worker/src/risk.ts`](../worker/src/risk.ts))

**Business context:** Today, an AI agent that wants to use a service or data from a new provider always hits the same wall: a human has to sign up and attach a credit card in advance, so the agent can't decide to buy a service on its own in the moment. Small providers also can't profitably charge tiny per-use amounts, because credit-card fees eat the whole transaction.

**Value delivered:** A system that lets a provider "set a price per use" and receive real payment from an AI agent instantly, with no signup flow and no card data collection — opening the door to a new "pay-as-your-agent-goes" business model on the Arc network.

**Success metric:** One real service is live for sale, and a test agent successfully buys → pays → receives it at least once, with the transaction verifiable on-chain.

---

## Story 1 — Provider sets a price and sells their own service

**As a** provider (owner of the data/tool)
**I want** to sell my service with a price set per call
**So that** I earn revenue on every use, with no subscription system or customer card storage to build

### Acceptance Criteria

**Scenario: Service goes live with a price, genuinely reachable**
- **Given** the provider has an endpoint ready to serve
- **When** the provider deploys the endpoint with a price set per use
- **Then** the service link must be reachable from the outside for real
- **And** the price per single use must be clearly stated in the system

**Scenario: Price changes later**
- **Given** the service is already live at one price
- **When** the provider updates the price
- **Then** the next service request must reflect the new price immediately, never the old one

---

## Story 2 — A customer who hasn't paid can't use the service

**As a** provider
**I want** the system to automatically reject access and state the price when no payment has been made
**So that** I don't lose revenue to people using the service for free

### Acceptance Criteria

**Scenario: Calling the service without paying**
- **Given** a user or agent has not paid
- **When** they call the service endpoint
- **Then** the system must respond with a "payment required" status, price, and payment details
- **And** must not return the real data/result

**Scenario: Reusing the same proof of payment**
- **Given** the same proof of payment is reused (replay)
- **When** the endpoint is called again with that same proof
- **Then** the system must reject the request and not grant access again without a fresh payment

---

## Story 3 — The AI agent pays for the service itself, with no human confirming

**As an** AI agent owner (the customer)
**I want** my agent to pay for the service it needs on its own, automatically
**So that** the agent can keep working without stopping to wait for me to confirm payment every time

### Acceptance Criteria

**Scenario: Agent pays successfully with no human intervening**
- **Given** the agent has been told the price it must pay by the system
- **When** the agent signs and broadcasts the payment transaction on-chain itself, automatically (the agent pays its own gas out of the same USDC used for the service fee — no intermediary pays on its behalf)
- **Then** the agent must receive the real result/data back
- **And** no human may confirm anything anywhere in the process

**Scenario: Agent pays the wrong or an incomplete amount**
- **Given** the agent sends a payment whose amount doesn't match the set price
- **When** the system checks the amount received
- **Then** the system must reject the request and not return any data
- **And** must tell the agent the reason for the rejection

---

## Story 4 — Payment genuinely reaches the provider, and is verifiable

**As a** provider
**I want** the money a customer pays to actually land in my account and be auditable afterward
**So that** I'm confident I received real revenue, not a simulation

### Acceptance Criteria

**Scenario: Auditing a transaction externally after the fact**
- **Given** one payment has already succeeded
- **When** that transaction is opened on a public block explorer
- **Then** the amount, the recipient (the provider), and the time must match what actually happened

**Scenario: The provider's balance genuinely increases**
- **Given** a payment has completed
- **When** the provider's balance is checked before and after the transaction
- **Then** the balance must increase by exactly the set price — no gas is deducted on the provider's side, because the agent pays its own gas separately from the amount transferred to us

---

## Story 5 — A grant reviewer can try it themselves and see it genuinely work

**As a** grant reviewer
**I want** to open a single link and see the whole system work end to end
**So that** I can judge that this project genuinely works, not just a paper concept

### Acceptance Criteria

**Scenario: Seeing the full flow from a single link**
- **Given** the reviewer has the repo link and the service link
- **When** they open the repo and run the demo script/video per the README's instructions
- **Then** they must see every step, from the agent requesting the service, paying, to getting the result
- **And** they must not need to contact the team for the system to work

**Scenario: Reaching the repo publicly with no special access**
- **Given** the reviewer has no special privileges
- **When** they open the repo link
- **Then** they must be able to clone or view the code immediately, with no extra access request

---

## Story 6 — The risk score must be computed from real on-chain data, never mocked

**As a** service consumer (agent) and as a grant reviewer
**I want** every factor in the risk score to be computed from the real on-chain data of the requested address
**So that** the result can genuinely be trusted, not just a good-looking number fixed in advance

### Acceptance Criteria

**Scenario: Different addresses produce different results based on real behavior**
- **Given** two addresses with genuinely different on-chain activity histories
- **When** the API is called for both addresses
- **Then** the factors and score returned must differ according to each address's real behavior, never a constant or random value

**Scenario: A factor with no real data source yet must honestly say so**
- **Given** some factor (e.g. contract source verification) has no verifiable data source wired up in the system yet
- **When** the API is called for an address that is a contract
- **Then** that factor must be reported as `unknown`, never guessed as `true` or `false`

Known v1 limitations (disclosed on purpose, not hidden) are listed in [`README.md`](../README.md#known-v1-limitations--stated-on-purpose-not-hidden)
