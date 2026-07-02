/**
 * Quick Scalp New Pool Strategy - High volume new pools
 * Pool < 30min, volume 5m > $50k, RSI 5m > 80
 * Tight 30 bin range, max hold 20min
 */
import { addStrategy } from '../strategy-library.js';

const QUICK_SCALP_STRATEGY = {
  id: 'quick_scalp_new_pool',
  name: 'Quick Scalp New High-Vol Pools',
  author: 'erika',
  lp_strategy: 'bid_ask',
  token_criteria: {
    pool_age_minutes: { min: 0, max: 30 },
    volume_5m_usd: { min: 50000 },
    rsi_5m: { min: 80 },
    notes: 'New pools with explosive early volume + overbought RSI confirmation'
  },
  entry: {
    condition: 'Pool age < 30min AND volume 5m >= $50k AND RSI 5m > 80',
    single_side: null,
    notes: 'Deploy immediately on signal match'
  },
  range: {
    type: 'tight',
    bins_below_pct: 100,
    bin_step: 30,
    notes: '30 bin tight range below active price'
  },
  exit: {
    max_hold_minutes: 20,
    take_profit_pct: 3,
    notes: 'Auto close after 20min OR 3% profit. No exceptions.'
  },
  best_for: 'Scalping new pools with momentum breakout'
};

export async function addQuickScalpStrategy() {
  const result = addStrategy(QUICK_SCALP_STRATEGY);
  console.log('Quick scalp strategy added:', result);
  return result;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  addQuickScalpStrategy().catch(console.error);
}
