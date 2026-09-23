// Static landing page served at GET /. Self-contained (no build step, no
// external runtime) — a plain string Hono returns as HTML. The "try it"
// panel calls this same Worker's own /risk/:address route live, so what a
// visitor sees is a real 402 response, not a screenshot or a fixture.
export const LANDING_HTML = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arc Risk Score — pay-per-call risk API for AI agents</title>
<meta name="description" content="Pay-per-call wallet risk-score API for AI agents on Arc mainnet. $0.01 USDC per lookup, settled by broadcasting your own payment — no facilitator.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #0B0C0E; color: #EDEFF2; font-family: 'Space Grotesk', system-ui, sans-serif; }
  .mono { font-family: 'JetBrains Mono', monospace; }
  a { color: #C6FF4D; }
  .wrap { width: 100%; max-width: 1160px; margin: 0 auto; padding: 0 24px; box-sizing: border-box; }
  .nav { display: flex; align-items: center; justify-content: space-between; padding: 28px 0 0; }
  .pill { display: flex; align-items: center; gap: 8px; padding: 6px 12px; border: 1px solid #23262B; border-radius: 999px; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: #5F5E5A; display: inline-block; }
  .dot.live { background: #C6FF4D; animation: pulse 1.8s ease-in-out infinite; }
  .dot.down { background: #FF6B6B; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
  @media (prefers-reduced-motion: reduce) { .dot.live { animation: none; } }
  h1 { font-size: clamp(32px, 4vw, 48px); line-height: 1.15; font-weight: 700; margin: 0 0 20px; max-width: 640px; }
  .accent { color: #C6FF4D; }
  p.lead { font-size: 17px; line-height: 1.7; color: #8B909A; max-width: 560px; margin: 0 0 28px; }
  .btn { font-family: inherit; font-size: 15px; font-weight: 500; padding: 13px 24px; border-radius: 8px; cursor: pointer; }
  .btn-primary { border: none; background: #C6FF4D; color: #0B0C0E; }
  .btn-ghost { border: 1px solid #23262B; background: transparent; color: #EDEFF2; text-decoration: none; display: inline-flex; align-items: center; }
  .card { background: #111316; border: 1px solid #23262B; border-radius: 12px; }
  .try-panel { padding: 22px 24px; margin: 0 0 72px; }
  .try-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
  input[type=text] { flex: 1 1 320px; min-width: 200px; background: #0B0C0E; border: 1px solid #23262B; color: #EDEFF2; border-radius: 8px; padding: 12px 14px; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
  input[type=text]::placeholder { color: #5F5E5A; }
  label { display: block; font-size: 12px; color: #8B909A; margin-bottom: 8px; }
  pre#result { margin: 0; padding: 16px; background: #0B0C0E; border-radius: 8px; font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-all; min-height: 20px; }
  .err { color: #FF6B6B; }
  .steps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; margin: 0 0 16px; }
  .step-n { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #C6FF4D; margin-bottom: 10px; }
  .step-t { font-size: 15px; font-weight: 500; margin-bottom: 6px; }
  .step-d { font-size: 13px; color: #8B909A; line-height: 1.6; }
  footer { border-top: 1px solid #23262B; padding: 28px 0 40px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #8B909A; }
  @media (max-width: 640px) { .steps { grid-template-columns: 1fr 1fr; } }
  .hero {
    position: relative;
    background:
      linear-gradient(180deg, rgba(11,12,14,.35) 0%, rgba(11,12,14,.75) 60%, #0B0C0E 100%),
      url('https://images.unsplash.com/photo-1644088379091-d574269d422f?auto=format&fit=crop&w=1600&q=70') center 30%/cover no-repeat;
    padding-bottom: 64px;
  }
  .credit { position: absolute; right: 24px; bottom: 16px; font-size: 10px; color: rgba(139,144,154,.7); }
  .credit a { color: rgba(139,144,154,.9); }
</style>
</head>
<body>
<div class="hero">
  <div class="wrap nav">
    <div class="mono" style="font-size:15px;font-weight:500;">ARC<span class="accent">·</span>RISK</div>
    <div class="pill"><span class="dot" id="status-dot"></span><span class="mono" id="status-text" style="font-size:12px;color:#8B909A;">checking arc mainnet&hellip;</span></div>
  </div>

  <div class="wrap" style="padding-top:88px;">
    <h1>Risk-score any Arc wallet <span class="accent">before your agent pays it.</span></h1>
    <p class="lead">A pay-per-call API for autonomous agents. $0.01 USDC per lookup, settled by the caller broadcasting its own EIP-3009 payment on Arc &mdash; no facilitator, no signup, no API key.</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <a class="btn btn-primary" href="https://github.com/kungpotato/solar-wind" target="_blank" rel="noopener">Source on GitHub</a>
    </div>
  </div>
  <div class="credit">Photo by <a href="https://unsplash.com/@choys_" target="_blank" rel="noopener">Conny Schneider</a> on <a href="https://unsplash.com" target="_blank" rel="noopener">Unsplash</a></div>
</div>

<div class="wrap">
  <div class="card try-panel">
    <label for="addr">Try it live &mdash; this calls this Worker's real /risk/:address endpoint, unpaid, right now</label>
    <div class="try-row">
      <input type="text" id="addr" class="mono" placeholder="0x... an Arc address" value="0x80771D0E7422d458a662a61bDDad97B48a97A8fd">
      <button class="btn btn-primary mono" id="go">Check price</button>
    </div>
    <pre id="result" class="mono"></pre>
  </div>
</div>

<div class="wrap">
  <div class="mono" style="font-size:12px;color:#8B909A;margin-bottom:24px;letter-spacing:.05em;">HOW IT WORKS</div>
  <div class="steps">
    <div><div class="step-n">01</div><div class="step-t">Agent calls the API</div><div class="step-d">A plain request to /risk/{address}, no key required.</div></div>
    <div><div class="step-n">02</div><div class="step-t">Server replies 402</div><div class="step-d">Price and payment details come back instead of data.</div></div>
    <div><div class="step-n">03</div><div class="step-t">Agent pays on Arc</div><div class="step-d">Signs &amp; broadcasts its own EIP-3009 tx &mdash; no facilitator.</div></div>
    <div><div class="step-n">04</div><div class="step-t">Score comes back</div><div class="step-d">Computed live from real on-chain activity.</div></div>
  </div>
  <p class="mono" style="font-size:12px;color:#5F5E5A;margin:0 0 72px;">Agents can skip reading this page &mdash; fetch <a href="/.well-known/x402.json" style="color:#5F5E5A;text-decoration:underline;">/.well-known/x402.json</a> to discover price and payment details automatically.</p>
</div>

<div class="wrap">
  <div class="mono" style="font-size:12px;color:#8B909A;margin-bottom:16px;letter-spacing:.05em;">PROOF IT WORKS</div>
  <p style="font-size:14px;line-height:1.7;color:#8B909A;max-width:640px;margin:0 0 72px;">
    A real $0.01 USDC payment already went through end to end on Arc mainnet &mdash;
    <a href="https://explorer.arc.io/tx/0x76c16c2c2167816d77b6705c01e37a03827f93de7ee00cbf17c3f02a748364fc" target="_blank" rel="noopener">see the transaction on Arc's own explorer</a>,
    or read the full writeup in the <a href="https://github.com/kungpotato/solar-wind#proof-it-works" target="_blank" rel="noopener">repo README</a>.
  </p>
</div>

<div class="wrap"><footer>
  <div>$0.01 / lookup &middot; USDC on Arc &middot; no facilitator</div>
  <a href="https://github.com/kungpotato/solar-wind">github.com/kungpotato/solar-wind &rarr;</a>
</footer></div>

<script>
(function () {
  var dot = document.getElementById('status-dot');
  var statusText = document.getElementById('status-text');
  fetch('/arc-status')
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.ok) {
        dot.className = 'dot live';
        statusText.textContent = 'arc mainnet · live · block ' + Number(data.blockNumber).toLocaleString();
      } else {
        throw new Error('not ok');
      }
    })
    .catch(function () {
      dot.className = 'dot down';
      statusText.textContent = 'arc mainnet · unreachable';
    });

  var btn = document.getElementById('go');
  var input = document.getElementById('addr');
  var out = document.getElementById('result');
  btn.addEventListener('click', function () {
    var addr = input.value.trim();
    if (!/^0x[0-9a-fA-F]{40}$/.test(addr)) {
      out.textContent = '';
      out.innerHTML = '<span class="err">Enter a valid 0x... Arc address first</span>';
      return;
    }
    out.textContent = 'GET /risk/' + addr + ' ...';
    fetch('/risk/' + addr)
      .then(function (res) {
        return res.text().then(function (body) {
          var line = 'HTTP ' + res.status + ' ' + (res.status === 402 ? 'Payment Required' : '') + '\\n';
          var reqHeader = res.headers.get('payment-required');
          if (reqHeader) {
            try {
              var decoded = JSON.parse(atob(reqHeader));
              line += JSON.stringify(decoded, null, 2);
            } catch (e) {
              line += body;
            }
          } else {
            line += body;
          }
          out.textContent = line;
        });
      })
      .catch(function (err) {
        out.innerHTML = '<span class="err">Request failed: ' + err.message + '</span>';
      });
  });
})();
</script>
</body>
</html>`
