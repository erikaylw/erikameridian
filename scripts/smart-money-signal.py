#!/usr/bin/env python3
"""Smart Money Signal Checker for Meridian
Monitors GMGN smart money buys → checks if tracked wallets are active → logs Meteora-ready signals"""

import json, subprocess, os, sys
from datetime import datetime

MERIDIAN = "/home/ubuntu/meridian"
SIGNAL_FILE = os.path.join(MERIDIAN, "smart-signals.json")
WALLETS_FILE = os.path.join(MERIDIAN, "smart-wallets.json")

# Load tracked wallets
tracked_wallets = {}
if os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE) as f:
        wdata = json.load(f)
    for w in wdata.get('wallets', []):
        tracked_wallets[w['address']] = w.get('name', w['address'][:8])

# Load existing signals
existing_signals = {}
if os.path.exists(SIGNAL_FILE):
    with open(SIGNAL_FILE) as f:
        sig_data = json.load(f)
    for sig in sig_data.get('signals', []):
        existing_signals[sig.get('token_address', '')] = sig

# Fetch smart money buy signals from GMGN
try:
    result = subprocess.run(
        ['gmgn-cli', 'market', 'signal', '--chain', 'sol',
         '--signal-type', '12', '--mc-min', '50000', '--mc-max', '5000000', '--raw'],
        capture_output=True, text=True, timeout=30
    )
    signals = json.loads(result.stdout) if result.stdout.strip() else []
except Exception as e:
    print(f"ERROR fetching signals: {e}", file=sys.stderr)
    signals = []

new_signals = []
tracked_hits = []

for s in signals:
    addr = s.get('token_address', '')
    data = s.get('data', {})
    exchange = data.get('exchange', '')
    ts = s.get('trigger_at', 0)
    mc = s.get('market_cap', 0)
    symbol = data.get('symbol', '?')
    name = data.get('name', '?')
    sm_wallets = data.get('smart_degen_wallets', [])

    if not addr or addr in existing_signals:
        continue

    # Check if any tracked wallet is in this signal
    for sw in sm_wallets:
        w_addr = sw.get('address', '')
        if w_addr in tracked_wallets:
            tracked_hits.append({
                'wallet': w_addr,
                'wallet_name': tracked_wallets[w_addr],
                'token': symbol,
                'token_address': addr,
                'amount_usd': sw.get('buy_amount', 0),
                'timestamp': ts
            })

    is_meteora = 'meteora' in exchange.lower() if exchange else False

    signal_entry = {
        'token_address': addr,
        'symbol': symbol,
        'name': name,
        'exchange': exchange,
        'market_cap': mc,
        'trigger_at': ts,
        'trigger_mc': s.get('trigger_mc', 0),
        'smart_degen_count': data.get('smart_degen_count', 0),
        'renowned_count': data.get('renowned_count', 0),
        'rug_ratio': data.get('rug_ratio', 0),
        'top_10_holder_rate': data.get('top_10_holder_rate', 0),
        'liquidity': data.get('liquidity', 0),
        'holder_count': data.get('holder_count', 0),
        'is_meteora_pool': is_meteora,
        'creator_token_status': data.get('creator_token_status', ''),
        'smart_degen_wallets': [w.get('address','') for w in sm_wallets],
        'detected_at': datetime.utcnow().isoformat()
    }
    new_signals.append(signal_entry)

# Merge new + existing, keep last 7 days
now_ts = datetime.utcnow().timestamp()
all_signals = {s['token_address']: s for s in list(existing_signals.values()) + new_signals}
all_signals = {k: v for k, v in all_signals.items() if v.get('trigger_at', 0) > now_ts - 7*86400}

# Save
output = {
    'last_updated': datetime.utcnow().isoformat(),
    'total_signals': len(all_signals),
    'signals': list(all_signals.values())
}
with open(SIGNAL_FILE, 'w') as f:
    json.dump(output, f, indent=2)

# === OUTPUT for cron delivery ===
print(f"🤖 Smart Money Signal Check — {datetime.utcnow().strftime('%H:%M UTC')}")

if tracked_hits:
    print(f"\n👀 TRACKED WALLETS ACTIVE ({len(tracked_hits)} hits):")
    for h in tracked_hits:
        print(f"  {h['wallet_name']} → {h['token']} (${h['amount_usd']:.0f})")

if new_signals:
    print(f"\n🆕 New smart money buys: {len(new_signals)}")

    meteora_ready = [s for s in new_signals if s['is_meteora_pool']]
    if meteora_ready:
        print(f"\n🔥 Meteora-ready ({len(meteora_ready)}):")
        for s in meteora_ready[:5]:
            print(f"  {s['symbol']} — MC ${s['market_cap']:.0f} | ${s['liquidity']:.0f} liq")

    strong = [s for s in new_signals if len(s.get('smart_degen_wallets',[])) >= 3 and s['rug_ratio'] < 0.2]
    if strong:
        print(f"\n💪 Strong cluster signals (≥3 SM):")
        for s in strong[:5]:
            sm_count = len(s.get('smart_degen_wallets',[]))
            print(f"  {s['symbol']} ({s['token_address'][:6]}...) — {sm_count} SM | MC ${s['market_cap']:.0f}")
else:
    print(f"No new signals. {len(all_signals)} cached.")

if not tracked_hits and not new_signals:
    print("Nothing to report.")
