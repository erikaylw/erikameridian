#!/usr/bin/env bash
# smart-money-signal.sh
# Cron: check GMGN smart money buys + our tracked wallets → Meteora pool check
set -euo pipefail

MERIDIAN_DIR="/home/ubuntu/meridian"
SIGNAL_FILE="$MERIDIAN_DIR/smart-signals.json"
WALLETS_FILE="$MERIDIAN_DIR/smart-wallets.json"
CACHE_FILE="$MERIDIAN_DIR/.last_signal_check"
NOW=$(date +%s)

# Ensure scripts dir exists
mkdir -p "$MERIDIAN_DIR/scripts"

# Load signal history
declare -A SEEN_SIGNALS
if [ -f "$CACHE_FILE" ]; then
    while IFS= read -r line; do
        SEEN_SIGNALS["$line"]=1
    done < "$CACHE_FILE"
fi

# Step 1: Get smart money buy signals (type 12) from GMGN
SIGNALS=$(gmgn-cli market signal --chain sol --signal-type 12 --mc-min 50000 --mc-max 5000000 --raw 2>/dev/null || echo "[]")

# Step 2: Filter for tokens with Meteora pools and smart money buys
NEW_SIGNALS=$(echo "$SIGNALS" | python3 -c "
import json, sys

data = json.load(sys.stdin) if sys.stdin.read().strip() else []
# reset stdin
sys.stdin = sys.__stdin__

# Actually re-read
" 2>/dev/null)

# Better approach: use python3 for the whole thing
python3 << 'PYEOF'
import json, subprocess, os, sys
from datetime import datetime

MERIDIAN = "/home/ubuntu/meridian"
CACHE_FILE = os.path.join(MERIDIAN, ".last_signal_check")
SIGNAL_FILE = os.path.join(MERIDIAN, "smart-signals.json")
WALLETS_FILE = os.path.join(MERIDIAN, "smart-wallets.json")

# Load tracked wallets
tracked_wallets = set()
if os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE) as f:
        wdata = json.load(f)
    for w in wdata.get('wallets', []):
        tracked_wallets.add(w['address'])

# Load existing signals
existing = {}
if os.path.exists(SIGNAL_FILE):
    with open(SIGNAL_FILE) as f:
        existing_data = json.load(f)
    for sig in existing_data.get('signals', []):
        existing[sig.get('token_address','')] = sig

# Fetch smart money buy signals
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
for s in signals:
    addr = s.get('token_address', '')
    data = s.get('data', {})
    exchange = data.get('exchange', '')
    timestamp = s.get('trigger_at', 0)
    mc = s.get('market_cap', 0)
    symbol = data.get('symbol', '?')
    name = data.get('name', '?')
    
    # Skip if already seen in last 24h
    if addr in existing:
        continue
    
    # Meteora or Raydium pools are deployable
    is_meteora = 'meteora' in exchange.lower() if exchange else False
    
    signal_entry = {
        'token_address': addr,
        'symbol': symbol,
        'name': name,
        'exchange': exchange,
        'market_cap': mc,
        'trigger_at': timestamp,
        'trigger_mc': s.get('trigger_mc', 0),
        'smart_degen_count': data.get('smart_degen_count', 0),
        'renowned_count': data.get('renowned_count', 0),
        'rug_ratio': data.get('rug_ratio', 0),
        'top_10_holder_rate': data.get('top_10_holder_rate', 0),
        'liquidity': data.get('liquidity', 0),
        'holder_count': data.get('holder_count', 0),
        'is_meteora_pool': is_meteora,
        'creator_token_status': data.get('creator_token_status', ''),
        'detected_at': datetime.utcnow().isoformat()
    }
    new_signals.append(signal_entry)

# Merge with existing
all_signals = existing.copy()
for ns in new_signals:
    all_signals[ns['token_address']] = ns

# Keep only last 7 days
cutoff = datetime.utcnow().timestamp() - (7 * 86400)
all_signals = {k: v for k, v in all_signals.items() if v.get('trigger_at', 0) > cutoff}

# Save
output = {
    'last_updated': datetime.utcnow().isoformat(),
    'signals': list(all_signals.values())
}
with open(SIGNAL_FILE, 'w') as f:
    json.dump(output, f, indent=2)

# Output summary for cron delivery
meteora_signals = [s for s in new_signals if s['is_meteora_pool'] and s['smart_degen_count'] > 0]
strong_signals = [s for s in new_signals if s['smart_degen_count'] >= 3 and s['rug_ratio'] < 0.2]

if new_signals:
    print(f"🤖 Smart Money Signal Check — {datetime.utcnow().strftime('%H:%M UTC')}")
    print(f"New smart money buys detected: {len(new_signals)}")
    
    if meteora_signals:
        print(f"\n🔥 Meteora-ready signals ({len(meteora_signals)}):")
        for s in meteora_signals[:5]:
            print(f"  {s['symbol']} — MC ${s['market_cap']:.0f} | SM: {s['smart_degen_count']} | Liq: ${s['liquidity']:.0f}")
    
    if strong_signals:
        print(f"\n💪 Strong signals (SM≥3, rug<0.2):")
        for s in strong_signals[:3]:
            print(f"  {s['symbol']} ({s['token_address'][:8]}...) — MC ${s['market_cap']:.0f}")
else:
    print(f"No new smart money signals. {len(all_signals)} active in cache.")

# Check if any tracked wallets appear in recent smartmoney trades
try:
    sm_result = subprocess.run(
        ['gmgn-cli', 'track', 'smartmoney', '--chain', 'sol', '--side', 'buy', '--raw'],
        capture_output=True, text=True, timeout=30
    )
    sm_trades = json.loads(sm_result.stdout) if sm_result.stdout.strip() else {}
    trade_list = sm_trades.get('list', []) if isinstance(sm_trades, dict) else sm_trades
except:
    trade_list = []

if trade_list:
    tracked_hits = []
    for t in trade_list[:50]:
        maker = t.get('maker', '')
        if maker in tracked_wallets:
            token_addr = t.get('base_address', '')
            sym = t.get('base_token', {}).get('symbol', '?')
            usd = t.get('amount_usd', 0)
            tracked_hits.append({
                'wallet': maker,
                'token': sym,
                'address': token_addr,
                'amount_usd': usd
            })
    
    if tracked_hits:
        print(f"\n👀 TRACKED WALLET ACTIVITY ({len(tracked_hits)}):")
        for h in tracked_hits:
            print(f"  {h['wallet'][:8]}... → {h['token']} (${h['amount_usd']:.0f})")

PYEOF
