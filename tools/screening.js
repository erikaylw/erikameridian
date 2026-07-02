import { config } from "../config.js";
import { isBlacklisted } from "../token-blacklist.js";
import { isDevBlocked, getBlockedDevs } from "../dev-blocklist.js";
import { log } from "../logger.js";
import { isBaseMintOnCooldown, isPoolOnCooldown } from "../pool-memory.js";
import { confirmIndicatorPreset } from "./chart-indicators.js";
import { getAgentMeridianBase, getAgentMeridianHeaders } from "./agent-meridian.js";
import { getRugcheckReport } from "./token.js";

const DATAPI_JUP = "https://datapi.jup.ag/v1";

const POOL_DISCOVERY_BASE = "https://pool-discovery-api.datapi.meteora.ag";
const PVP_SHORTLIST_LIMIT = 2;
const PVP_RIVAL_LIMIT = 2;
const PVP_MIN_ACTIVE_TVL = 5_000;
const PVP_MIN_HOLDERS = 500;
const PVP_MIN_GLOBAL_FEES_SOL = 30;
const SOL_MINT = "So11111111111111111111111111111111111111112";

function isSolQuotePool(pool) {
  const quoteSymbol = String(pool.quote?.symbol || "").trim().toUpperCase();
  const quoteMint = pool.quote?.mint || null;
  return quoteSymbol === "SOL" || quoteMint === SOL_MINT;
}


function normalizeSymbol(symbol) {
  return String(symbol || "").trim().toUpperCase();
}

function scoreCandidate(pool) {
  const feeTvl = Number(pool.fee_active_tvl_ratio || 0);
  const organic = Number(pool.organic_score || 0);
  const volume = Number(pool.volume_window || 0);
  const holders = Number(pool.holders || 0);
  // Soft bonuses — KOL cluster presence and smart money buy signal
  // These are 0 before OKX enrichment, so initial sort is unaffected.
  // A re-sort after enrichment surfaces these pools to the top.
  const kolBonus        = pool.kol_in_clusters  ? 500 : 0;
  const smartMoneyBonus = pool.smart_money_buy   ? 300 : 0;
  return feeTvl * 1000 + organic * 10 + volume / 100 + holders / 100 + kolBonus + smartMoneyBonus;
}

async function fetchDiscordSignalCandidates() {
  const res = await fetch(`${getAgentMeridianBase()}/signals/discord/candidates`, {
    headers: getAgentMeridianHeaders(),
  });
  if (!res.ok) throw new Error(`discord signal candidates ${res.status}`);
  const data = await res.json();
  return Array.isArray(data?.candidates) ? data.candidates : [];
}

async function searchAssetsBySymbol(symbol) {
  const res = await fetch(`${DATAPI_JUP}/assets/search?query=${encodeURIComponent(symbol)}`);
  if (!res.ok) throw new Error(`assets/search ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : [data];
}

async function findRivalPool(mint) {
  const url = `https://dlmm.datapi.meteora.ag/pools?query=${encodeURIComponent(mint)}&sort_by=${encodeURIComponent("tvl:desc")}&filter_by=${encodeURIComponent(`tvl>${PVP_MIN_ACTIVE_TVL}`)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`rival pool search ${res.status}`);
  const data = await res.json();
  const pools = Array.isArray(data?.data) ? data.data : [];
  return pools.find((pool) => pool?.token_x?.address === mint || pool?.token_y?.address === mint) || null;
}

async function enrichPvpRisk(pools) {
  const shortlist = [...pools]
    .sort((a, b) => scoreCandidate(b) - scoreCandidate(a))
    .slice(0, PVP_SHORTLIST_LIMIT);

  if (shortlist.length === 0) return;

  const symbolCache = new Map();

  await Promise.all(shortlist.map(async (pool) => {
    const symbol = normalizeSymbol(pool.base?.symbol);
    const ownMint = pool.base?.mint;
    if (!symbol || !ownMint) return;

    let assets = symbolCache.get(symbol);
    if (!assets) {
      assets = await searchAssetsBySymbol(symbol).catch(() => []);
      symbolCache.set(symbol, assets);
    }

    const rivalAssets = assets
      .filter((asset) => normalizeSymbol(asset?.symbol) === symbol && asset?.id && asset.id !== ownMint)
      .sort((a, b) => Number(b?.liquidity || 0) - Number(a?.liquidity || 0))
      .slice(0, PVP_RIVAL_LIMIT);

    for (const rival of rivalAssets) {
      const rivalHolders = Number(rival?.holderCount || 0);
      const rivalFees = Number(rival?.fees || 0);
      if (rivalHolders < PVP_MIN_HOLDERS || rivalFees < PVP_MIN_GLOBAL_FEES_SOL) continue;

      const rivalPool = await findRivalPool(rival.id).catch(() => null);
      if (!rivalPool) continue;

      pool.is_pvp = true;
      pool.pvp_risk = "high";
      pool.pvp_symbol = pool.base?.symbol || symbol;
      pool.pvp_rival_name = rival?.name || pool.pvp_symbol;
      pool.pvp_rival_mint = rival.id;
      pool.pvp_rival_pool = rivalPool.address;
      pool.pvp_rival_tvl = round(Number(rivalPool.tvl || 0));
      pool.pvp_rival_holders = rivalHolders;
      pool.pvp_rival_fees = Number(rivalFees.toFixed(2));
      log("screening", `PVP guard: ${pool.name} has active rival ${pool.pvp_rival_name} (${rival.id.slice(0, 8)})`);
      break;
    }
  }));
}



// bin_step=100, fee_pct ≈ 2% or 3% (tolerance ±0.5)
const FAST_TRACK_BIN_STEPS = [100];
const FAST_TRACK_FEE_PCTS  = [2, 3];

/**
 * Fetch new high-volume pools with relaxed quality filters.
 * Used for the fast-track path: new pools (< N hours) with specific bin/fee and high volume
 * bypass the normal holders/organic/mcap requirements.
 */
async function fetchFastTrackPools({ maxAgeHours, minVolume }) {
  const s = config.screening;
  const ageThreshold = Date.now() - maxAgeHours * 3_600_000;

  const filters = [
    "base_token_has_critical_warnings=false",
    "quote_token_has_critical_warnings=false",
    "pool_type=dlmm",
    `dlmm_bin_step>=${Math.min(...FAST_TRACK_BIN_STEPS)}`,
    `dlmm_bin_step<=${Math.max(...FAST_TRACK_BIN_STEPS)}`,
    `volume>=${minVolume}`,
    `tvl>=${s.minTvl}`,
    `base_token_created_at>=${ageThreshold}`,
  ].join("&&");

  const useServerDiscovery = !!config.api.publicApiKey;
  const url = useServerDiscovery
    ? `${getAgentMeridianBase()}/discovery/pools?page_size=20&filter_by=${encodeURIComponent(filters)}&timeframe=${s.timeframe}&category=${s.category}`
    : `${POOL_DISCOVERY_BASE}/pools?page_size=20&filter_by=${encodeURIComponent(filters)}&timeframe=${s.timeframe}&category=${s.category}`;

  const res = await fetch(url, { headers: useServerDiscovery ? getAgentMeridianHeaders() : {} });
  if (!res.ok) {
    log("screening", `Fast-track discovery failed: ${res.status}`);
    return [];
  }

  const data = await res.json();
  const raw = Array.isArray(data.data) ? data.data : [];

  return raw.map(condensePool).filter((p) => {
    // Enforce exact fee_pct match (±0.5 tolerance for rounding)
    if (!FAST_TRACK_FEE_PCTS.some((f) => p.fee_pct != null && Math.abs(p.fee_pct - f) <= 0.5)) return false;
    // Enforce age again in-code (token_age_hours from condensed pool)
    if (p.token_age_hours != null && p.token_age_hours > maxAgeHours) return false;
    return true;
  });
}

/**
 * Fetch pools from the Meteora Pool Discovery API.
 * Returns condensed data optimized for LLM consumption (saves tokens).
 */
export async function discoverPools({
  page_size = 50,
} = {}) {
  const s = config.screening;
  const filters = [
    "base_token_has_critical_warnings=false",
    "quote_token_has_critical_warnings=false",
    s.excludeHighSupplyConcentration ? "base_token_has_high_supply_concentration=false" : null,
    "base_token_has_high_single_ownership=false",
    "pool_type=dlmm",
    `base_token_market_cap>=${s.minMcap}`,
    `base_token_market_cap<=${s.maxMcap}`,
    `base_token_holders>=${s.minHolders}`,
    `volume>=${s.minVolume}`,
    `tvl>=${s.minTvl}`,
    s.maxTvl != null ? `tvl<=${s.maxTvl}` : null,
    `dlmm_bin_step>=${s.minBinStep}`,
    `dlmm_bin_step<=${s.maxBinStep}`,
    `fee_active_tvl_ratio>=${s.minFeeActiveTvlRatio}`,
    `base_token_organic_score>=${s.minOrganic}`,
    `quote_token_organic_score>=${s.minQuoteOrganic}`,
    s.minTokenAgeHours != null ? `base_token_created_at<=${Date.now() - s.minTokenAgeHours * 3_600_000}` : null,
    s.maxTokenAgeHours != null ? `base_token_created_at>=${Date.now() - s.maxTokenAgeHours * 3_600_000}` : null,
    Array.isArray(s.allowedLaunchpads) && s.allowedLaunchpads.length > 0
      ? `base_token_launchpad=[${s.allowedLaunchpads.join(",")}]`
      : null,
  ].filter(Boolean).join("&&");

  const useServerDiscovery = !!config.api.publicApiKey;
  const url = useServerDiscovery
    ? `${getAgentMeridianBase()}/discovery/pools?` +
      `page_size=${page_size}` +
      `&filter_by=${encodeURIComponent(filters)}` +
      `&timeframe=${s.timeframe}` +
      `&category=${s.category}`
    : `${POOL_DISCOVERY_BASE}/pools?` +
      `page_size=${page_size}` +
      `&filter_by=${encodeURIComponent(filters)}` +
      `&timeframe=${s.timeframe}` +
      `&category=${s.category}`;

  const res = await fetch(url, {
    headers: useServerDiscovery ? getAgentMeridianHeaders() : {},
  });

  if (!res.ok) {
    throw new Error(`Pool Discovery API error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();

  let rawPools = Array.isArray(data.data) ? data.data : [];

  if (config.screening.useDiscordSignals) {
    const signalCandidates = await fetchDiscordSignalCandidates().catch((error) => {
      log("screening", `Discord signal fetch failed: ${error.message}`);
      return [];
    });
    const signalPools = signalCandidates
      .map((candidate) => {
        const discoveryPool = candidate.discovery_pool;
        if (!discoveryPool?.pool_address) return null;
        return {
          ...discoveryPool,
          discord_signal: true,
          discord_signal_count: candidate.source_count || 1,
          discord_signal_seen_count: candidate.seen_count || 1,
          discord_signal_first_seen_at: candidate.first_seen_at || null,
          discord_signal_last_seen_at: candidate.last_seen_at || null,
        };
      })
      .filter(Boolean);

    if (config.screening.discordSignalMode === "only") {
      rawPools = signalPools;
    } else if (signalPools.length > 0) {
      const byPool = new Map(rawPools.map((pool) => [pool.pool_address, pool]));
      for (const signalPool of signalPools) {
        if (byPool.has(signalPool.pool_address)) {
          byPool.set(signalPool.pool_address, {
            ...byPool.get(signalPool.pool_address),
            discord_signal: true,
            discord_signal_count: signalPool.discord_signal_count,
            discord_signal_seen_count: signalPool.discord_signal_seen_count,
            discord_signal_first_seen_at: signalPool.discord_signal_first_seen_at,
            discord_signal_last_seen_at: signalPool.discord_signal_last_seen_at,
          });
        } else {
          byPool.set(signalPool.pool_address, signalPool);
        }
      }
      rawPools = Array.from(byPool.values());
    }
  }

  const condensed = rawPools.map(condensePool);

  // Hard-filter blacklisted tokens and blocked deployers (what pool discovery already gave us)
  let pools = condensed.filter((p) => {
    if (isBlacklisted(p.base?.mint)) {
      log("blacklist", `Filtered blacklisted token ${p.base?.symbol} (${p.base?.mint?.slice(0, 8)}) in pool ${p.name}`);
      return false;
    }
    if (p.dev && isDevBlocked(p.dev)) {
      log("dev_blocklist", `Filtered blocked deployer ${p.dev?.slice(0, 8)} token ${p.base?.symbol} in pool ${p.name}`);
      return false;
    }
    return true;
  });

  const filtered = condensed.length - pools.length;
  if (filtered > 0) log("blacklist", `Filtered ${filtered} pool(s) with blacklisted tokens/devs`);

  // If pool discovery didn't supply dev field, batch-fetch from Jupiter for any pools
  // where dev is null — but only if the dev blocklist is non-empty (avoid useless calls)
  const blockedDevs = getBlockedDevs();
  if (Object.keys(blockedDevs).length > 0) {
    const missingDev = pools.filter((p) => !p.dev && p.base?.mint);
    if (missingDev.length > 0) {
      const devResults = await Promise.allSettled(
        missingDev.map((p) =>
          fetch(`${DATAPI_JUP}/assets/search?query=${p.base.mint}`)
            .then((r) => r.ok ? r.json() : null)
            .then((d) => {
              const t = Array.isArray(d) ? d[0] : d;
              return { pool: p.pool, dev: t?.dev || null };
            })
            .catch(() => ({ pool: p.pool, dev: null }))
        )
      );
      const devMap = {};
      for (const r of devResults) {
        if (r.status === "fulfilled") devMap[r.value.pool] = r.value.dev;
      }
      pools = pools.filter((p) => {
        const dev = devMap[p.pool];
        if (dev) p.dev = dev; // enrich in-place
        if (dev && isDevBlocked(dev)) {
          log("dev_blocklist", `Filtered blocked deployer (jup) ${dev.slice(0, 8)} token ${p.base?.symbol}`);
          return false;
        }
        return true;
      });
    }
  }

  return {
    total: data.total,
    pools,
  };
}

/**
 * Returns eligible pools for the agent to evaluate and pick from.
 * Hard filters applied in code, agent decides which to deploy into.
 */
export async function getTopCandidates({ limit = 10 } = {}) {
  const { config } = await import("../config.js");
  const { pools } = await discoverPools({ page_size: 50 });
  const filteredOut = [];

  // Exclude pools where the wallet already has an open position
  const { getMyPositions } = await import("./dlmm.js");
  const { positions } = await getMyPositions();
  const occupiedPools = new Set(positions.map((p) => p.pool));
  const occupiedMints = new Set(positions.map((p) => p.base_mint).filter(Boolean));

  const eligible = pools
    .filter((p) => {
      if (occupiedPools.has(p.pool)) {
        pushFilteredReason(filteredOut, p, "already have an open position in this pool");
        return false;
      }
      if (occupiedMints.has(p.base?.mint)) {
        pushFilteredReason(filteredOut, p, "already holding this base token in another pool");
        return false;
      }
      if (isPoolOnCooldown(p.pool)) {
        log("screening", `Filtered cooldown pool ${p.name} (${p.pool.slice(0, 8)})`);
        pushFilteredReason(filteredOut, p, "pool cooldown active");
        return false;
      }
      if (isBaseMintOnCooldown(p.base?.mint)) {
        log("screening", `Filtered cooldown token ${p.base?.symbol} (${p.base?.mint?.slice(0, 8)})`);
        pushFilteredReason(filteredOut, p, "token cooldown active");
        return false;
      }
      if (config.screening.solQuoteOnly !== false && !isSolQuotePool(p)) {
        const quote = p.quote?.symbol || p.quote?.mint || "unknown";
        log("screening", `Filtered non-SOL quote pool ${p.name}: quote=${quote}`);
        pushFilteredReason(filteredOut, p, `quote ${quote} is not SOL`);
        return false;
      }
      const minRealtimeFeeTvl = config.screening.minRealtimeFeeTvlRatio;
      if (minRealtimeFeeTvl != null && Number(p.fee_active_tvl_ratio || 0) < minRealtimeFeeTvl) {
        log("screening", `Filtered weak real-time fee/TVL ${p.name}: ${p.fee_active_tvl_ratio ?? 0}% < ${minRealtimeFeeTvl}%`);
        pushFilteredReason(filteredOut, p, `real-time fee/TVL ${p.fee_active_tvl_ratio ?? 0}% below ${minRealtimeFeeTvl}% minimum`);
        return false;
      }
      const minVol5m = config.screening.minVolume5m;
      if (minVol5m != null && (p.volume_window == null || p.volume_window < minVol5m)) {
        log("screening", `Filtered low 5m volume ${p.name}: $${p.volume_window ?? 0} < $${minVol5m}`);
        pushFilteredReason(filteredOut, p, `5m volume $${p.volume_window ?? 0} below $${minVol5m} minimum`);
        return false;
      }
      return true;
    })
    .sort((a, b) => scoreCandidate(b) - scoreCandidate(a))
    .slice(0, limit);

  if (config.screening.avoidPvpSymbols && eligible.length > 0) {
    await enrichPvpRisk(eligible);
    if (config.screening.blockPvpSymbols) {
      const before = eligible.length;
      const pvpRemoved = eligible.filter((p) => p.is_pvp);
      pvpRemoved.forEach((p) => pushFilteredReason(filteredOut, p, "PVP hard filter"));
      eligible.splice(0, eligible.length, ...eligible.filter((p) => !p.is_pvp));
      if (eligible.length < before) {
        log("screening", `PVP hard filter removed ${before - eligible.length} pool(s)`);
      }
    }
  }

  // Enrich with OKX data — advanced info (risk/bundle/sniper) + ATH price (no API key required)
  if (eligible.length > 0) {
    const { getAdvancedInfo, getPriceInfo, getClusterList, getRiskFlags } = await import("./okx.js");
    const okxResults = await Promise.allSettled(
      eligible.map(async (p) => {
        if (!p.base?.mint) return { adv: null, price: null, clusters: [], risk: null };
        const [adv, price, clusters, risk] = await Promise.allSettled([
          getAdvancedInfo(p.base.mint),
          getPriceInfo(p.base.mint),
          getClusterList(p.base.mint),
          getRiskFlags(p.base.mint),
        ]);

        const mintShort = p.base.mint.slice(0, 8);
        if (adv.status !== "fulfilled")      log("okx", `advanced-info unavailable for ${p.name} (${mintShort})`);
        if (price.status !== "fulfilled")    log("okx", `price-info unavailable for ${p.name} (${mintShort})`);
        if (clusters.status !== "fulfilled") log("okx", `cluster-list unavailable for ${p.name} (${mintShort})`);
        if (risk.status !== "fulfilled")     log("okx", `risk-check unavailable for ${p.name} (${mintShort})`);

        return {
          adv: adv.status === "fulfilled" ? adv.value : null,
          price: price.status === "fulfilled" ? price.value : null,
          clusters: clusters.status === "fulfilled" ? clusters.value : [],
          risk: risk.status === "fulfilled" ? risk.value : null,
        };
      })
    );
    for (let i = 0; i < eligible.length; i++) {
      const r = okxResults[i];
      if (r.status !== "fulfilled") continue;
      const { adv, price, clusters, risk } = r.value;
      if (adv) {
        eligible[i].risk_level      = adv.risk_level;
        eligible[i].bundle_pct      = adv.bundle_pct;
        eligible[i].sniper_pct      = adv.sniper_pct;
        eligible[i].suspicious_pct  = adv.suspicious_pct;
        eligible[i].smart_money_buy = adv.smart_money_buy;
        eligible[i].dev_sold_all    = adv.dev_sold_all;
        eligible[i].dex_boost       = adv.dex_boost;
        eligible[i].dex_screener_paid = adv.dex_screener_paid;
        if (adv.creator && !eligible[i].dev) eligible[i].dev = adv.creator;
      }
      if (risk) {
        eligible[i].is_rugpull = risk.is_rugpull;
        eligible[i].is_wash    = risk.is_wash;
      }
      if (price) {
        eligible[i].price_vs_ath_pct = price.price_vs_ath_pct;
        eligible[i].ath              = price.ath;
      }
      if (clusters?.length) {
        // Surface KOL presence and top cluster trend for LLM
        eligible[i].kol_in_clusters      = clusters.some((c) => c.has_kol);
        eligible[i].top_cluster_trend    = clusters[0]?.trend ?? null;      // buy|sell|neutral
        eligible[i].top_cluster_hold_pct = clusters[0]?.holding_pct ?? null;
      }
    }

    // Re-rank now that KOL / smart-money signals are populated.
    // Pools with KOL clusters (+500) or smart money buys (+300) bubble to the top.
    eligible.sort((a, b) => scoreCandidate(b) - scoreCandidate(a));
    const kolCount  = eligible.filter((p) => p.kol_in_clusters).length;
    const smCount   = eligible.filter((p) => p.smart_money_buy).length;
    log("screening", `Signal re-rank complete — ${kolCount} KOL pool(s), ${smCount} smart-money pool(s) among ${eligible.length} candidates`);

    // Wash trading hard filter — fake volume = misleading fee yield
    eligible.splice(0, eligible.length, ...eligible.filter((p) => {
      if (p.is_wash) {
        log("screening", `Risk filter: dropped ${p.name} — wash trading flagged`);
        pushFilteredReason(filteredOut, p, "wash trading flagged");
        return false;
      }
      return true;
    }));

    // ── RugCheck enrichment — insider %, rug score, dev hold ─────────
    const needsRugcheck = eligible.length > 0 && (
      config.screening.maxInsiderPct   != null ||
      config.screening.maxRugRatio     != null ||
      config.screening.maxDevHoldPct   != null
    );
    if (needsRugcheck) {
      log("screening", `RugCheck: fetching security data for ${eligible.length} pool(s)...`);
      const rugResults = await Promise.allSettled(
        eligible.map((p) => p.base?.mint ? getRugcheckReport(p.base.mint) : Promise.resolve(null))
      );
      for (let i = 0; i < eligible.length; i++) {
        const r = rugResults[i];
        if (r.status !== "fulfilled" || !r.value) continue;
        const rc = r.value;
        eligible[i].rc_rug_score        = rc.rug_score;
        eligible[i].rc_insider_pct      = rc.insider_pct;
        eligible[i].rc_creator_hold_pct = rc.creator_hold_pct;
        eligible[i].rc_lp_locked_pct    = rc.lp_locked_pct;
        eligible[i].rc_risks            = rc.risks;
        if (rc.top10_pct > 0 && eligible[i].top10_pct == null) {
          eligible[i].top10_pct = rc.top10_pct; // backfill if not from Jupiter
        }
      }

      // Insider % filter
      const maxInsiderPct = config.screening.maxInsiderPct;
      if (maxInsiderPct != null) {
        const before = eligible.length;
        eligible.splice(0, eligible.length, ...eligible.filter((p) => {
          if (p.rc_insider_pct != null && p.rc_insider_pct > maxInsiderPct) {
            log("screening", `Insider filter: dropped ${p.name} — insider ${p.rc_insider_pct}% > ${maxInsiderPct}%`);
            pushFilteredReason(filteredOut, p, `insider wallets ${p.rc_insider_pct}% > ${maxInsiderPct}% limit`);
            return false;
          }
          return true;
        }));
        if (eligible.length < before) log("screening", `Insider filter removed ${before - eligible.length} pool(s)`);
      }

      // Rug score filter (0-100, higher = riskier)
      const maxRugRatio = config.screening.maxRugRatio;
      if (maxRugRatio != null) {
        const rugThreshold = maxRugRatio <= 1 ? maxRugRatio * 100 : maxRugRatio; // support both 0.3 and 30
        const before = eligible.length;
        eligible.splice(0, eligible.length, ...eligible.filter((p) => {
          if (p.rc_rug_score != null && p.rc_rug_score > rugThreshold) {
            log("screening", `Rug score filter: dropped ${p.name} — rug score ${p.rc_rug_score} > ${rugThreshold}`);
            pushFilteredReason(filteredOut, p, `rug score ${p.rc_rug_score} > ${rugThreshold} limit`);
            return false;
          }
          return true;
        }));
        if (eligible.length < before) log("screening", `Rug score filter removed ${before - eligible.length} pool(s)`);
      }

      // Dev/creator hold % filter
      const maxDevHoldPct = config.screening.maxDevHoldPct;
      if (maxDevHoldPct != null) {
        const before = eligible.length;
        eligible.splice(0, eligible.length, ...eligible.filter((p) => {
          if (p.rc_creator_hold_pct != null && p.rc_creator_hold_pct > maxDevHoldPct) {
            log("screening", `Dev hold filter: dropped ${p.name} — creator holds ${p.rc_creator_hold_pct}% > ${maxDevHoldPct}%`);
            pushFilteredReason(filteredOut, p, `creator holds ${p.rc_creator_hold_pct}% > ${maxDevHoldPct}% limit`);
            return false;
          }
          return true;
        }));
        if (eligible.length < before) log("screening", `Dev hold filter removed ${before - eligible.length} pool(s)`);
      }
    }

    // ATH filter — drop pools where price is too close to ATH
    const athFilter = config.screening.athFilterPct;
    if (athFilter != null) {
      const threshold = 100 + athFilter; // e.g. -20 → threshold = 80 (price must be <= 80% of ATH)
      const before = eligible.length;
      eligible.splice(0, eligible.length, ...eligible.filter((p) => {
        if (p.price_vs_ath_pct == null) return true; // no data → don't filter
        if (p.price_vs_ath_pct > threshold) {
          log("screening", `ATH filter: dropped ${p.name} — ${p.price_vs_ath_pct}% of ATH (limit: ${threshold}%)`);
          pushFilteredReason(filteredOut, p, `${p.price_vs_ath_pct}% of ATH > ${threshold}% limit`);
          return false;
        }
        return true;
      }));
      if (eligible.length < before) log("screening", `ATH filter removed ${before - eligible.length} pool(s)`);
    }

    // Suspicious wallet % filter (OKX advanced) — proxy for insider concentration
    const maxSuspPct = config.screening.maxSuspiciousPct;
    if (maxSuspPct != null) {
      const beforeSusp = eligible.length;
      eligible.splice(0, eligible.length, ...eligible.filter((p) => {
        if (p.suspicious_pct != null && p.suspicious_pct > maxSuspPct) {
          log("screening", `Suspicious filter: dropped ${p.name} — suspicious wallets ${p.suspicious_pct}% > ${maxSuspPct}%`);
          pushFilteredReason(filteredOut, p, `suspicious wallets ${p.suspicious_pct}% > ${maxSuspPct}% limit`);
          return false;
        }
        return true;
      }));
      if (eligible.length < beforeSusp) log("screening", `Suspicious filter removed ${beforeSusp - eligible.length} pool(s)`);
    }

    // Drop any pools whose creator is on the dev blocklist (caught via advanced-info)
    const before = eligible.length;
    const filtered = eligible.filter((p) => {
      if (p.dev && isDevBlocked(p.dev)) {
        log("dev_blocklist", `Filtered blocked deployer (okx) ${p.dev.slice(0, 8)} token ${p.base?.symbol}`);
        pushFilteredReason(filteredOut, p, "blocked deployer");
        return false;
      }
      return true;
    });
    eligible.splice(0, eligible.length, ...filtered);
    if (eligible.length < before) log("dev_blocklist", `Filtered ${before - eligible.length} pool(s) via OKX creator check`);
  }

  // ── 24h fee/TVL filter — ensures pool has been consistently active, not just a 5m spike ──
  const minFee24h = config.screening.minFee24hTvlRatio;
  if (minFee24h != null && eligible.length > 0) {
    const results24h = await Promise.allSettled(
      eligible.map((p) => getPoolDetail({ pool_address: p.pool, timeframe: "24h" }))
    );
    const before24h = eligible.length;
    eligible.splice(0, eligible.length, ...eligible.filter((p, i) => {
      const r = results24h[i];
      if (r.status !== "fulfilled") return true; // API error → don't penalise
      const raw = r.value;
      const ratio = raw.fee_active_tvl_ratio > 0
        ? raw.fee_active_tvl_ratio
        : (raw.active_tvl > 0 ? (raw.fee / raw.active_tvl) * 100 : null);
      if (ratio == null) return true; // no data → don't filter
      p.fee_active_tvl_ratio_24h = Number(ratio.toFixed(4));
      if (ratio < minFee24h) {
        log("screening", `24h fee/TVL filter: dropped ${p.name} — ${ratio.toFixed(2)}% < ${minFee24h}%`);
        pushFilteredReason(filteredOut, p, `24h fee/TVL ${ratio.toFixed(2)}% below ${minFee24h}% minimum`);
        return false;
      }
      return true;
    }));
    if (eligible.length < before24h) log("screening", `24h fee/TVL filter removed ${before24h - eligible.length} pool(s)`);
  }

  if (config.indicators.enabled && eligible.length > 0) {
    const confirmations = await Promise.all(
      eligible.map(async (pool) => {
        try {
          const confirmation = await confirmIndicatorPreset({
            mint: pool.base?.mint,
            side: "entry",
          });
          return { pool: pool.pool, confirmation };
        } catch (error) {
          return {
            pool: pool.pool,
            confirmation: {
              enabled: true,
              confirmed: true,
              skipped: true,
              reason: `Indicator confirmation unavailable: ${error.message}`,
              intervals: [],
            },
          };
        }
      }),
    );
    const confirmationByPool = new Map(confirmations.map((entry) => [entry.pool, entry.confirmation]));
    const before = eligible.length;
    const confirmedEligible = eligible.filter((pool) => {
      const confirmation = confirmationByPool.get(pool.pool);
      pool.indicator_confirmation = confirmation || null;
      if (!confirmation || confirmation.confirmed) return true;
      pushFilteredReason(filteredOut, pool, `indicator reject: ${confirmation.reason}`);
      log("screening", `Indicator rejected ${pool.name} (${pool.pool.slice(0, 8)}): ${confirmation.reason}`);
      return false;
    });
    eligible.splice(0, eligible.length, ...confirmedEligible);
    if (eligible.length < before) {
      log("screening", `Indicator confirmation removed ${before - eligible.length} candidate(s)`);
    }
  }

  // ── Fast-track: new pools with high volume + specific bin/fee config ─────
  if (config.screening.fastTrackEnabled !== false) {
    const ftMaxAge = config.screening.fastTrackMaxAgeHours ?? 3;
    const ftMinVol = config.screening.fastTrackMinVolume   ?? 40_000;
    const ftMinBins = config.screening.fastTrackMinBins    ?? 40;

    try {
      const ftPools = await fetchFastTrackPools({ maxAgeHours: ftMaxAge, minVolume: ftMinVol });
      const eligibleByPool = new Map(eligible.map((e) => [e.pool, e]));

      for (const p of ftPools) {
        // Skip blacklisted, blocked devs, OOR/pool cooldowns, occupied pools/mints
        if (isBlacklisted(p.base?.mint)) continue;
        if (p.dev && isDevBlocked(p.dev)) continue;
        if (isPoolOnCooldown(p.pool)) continue;
        if (isBaseMintOnCooldown(p.base?.mint)) continue;
        if (occupiedPools.has(p.pool)) continue;
        if (occupiedMints.has(p.base?.mint)) continue;

        p.fast_track = true;
        p.fast_track_min_bins = ftMinBins;
        p.fast_track_reason = `New pool (${p.token_age_hours ?? "?"}h old), bin_step=${p.bin_step}, fee=${p.fee_pct}%, vol=$${p.volume_window?.toLocaleString() ?? "?"}`;

        if (eligibleByPool.has(p.pool)) {
          // Already in normal candidates — just tag it
          Object.assign(eligibleByPool.get(p.pool), {
            fast_track: true,
            fast_track_min_bins: ftMinBins,
            fast_track_reason: p.fast_track_reason,
          });
        } else {
          eligible.push(p);
          log("screening", `Fast-track candidate: ${p.name} (${p.pool.slice(0, 8)}) — ${p.fast_track_reason}`);
        }
      }
    } catch (e) {
      log("screening", `Fast-track discovery error: ${e.message}`);
    }
  }

  return {
    candidates: eligible,
    total_screened: pools.length,
    filtered_examples: filteredOut.slice(0, 3),
  };
}

/**
 * Get full raw details for a specific pool.
 * Fetches top 50 pools from discovery API and finds the matching address.
 * Returns the full unfiltered API object (all fields, not condensed).
 */
export async function getPoolDetail({ pool_address, timeframe = "5m" }) {
  const useServerDiscovery = !!config.api.publicApiKey;
  const url = useServerDiscovery
    ? `${getAgentMeridianBase()}/discovery/pools/${pool_address}?timeframe=${encodeURIComponent(timeframe)}`
    : `${POOL_DISCOVERY_BASE}/pools?` +
      `page_size=1` +
      `&filter_by=${encodeURIComponent(`pool_address=${pool_address}`)}` +
      `&timeframe=${timeframe}`;

  const res = await fetch(url, {
    headers: useServerDiscovery ? getAgentMeridianHeaders() : {},
  });

  if (!res.ok) {
    throw new Error(`Pool detail API error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  const pool = useServerDiscovery ? data : (data.data || [])[0];

  if (!pool) {
    throw new Error(`Pool ${pool_address} not found`);
  }

  return pool;
}

/**
 * Condense a pool object for LLM consumption.
 * Raw API returns ~100+ fields per pool. The LLM only needs ~20.
 */
function condensePool(p) {
  return {
    pool: p.pool_address,
    name: p.name,
    base: {
      symbol: p.token_x?.symbol,
      mint: p.token_x?.address,
      organic: Math.round(p.token_x?.organic_score || 0),
      warnings: p.token_x?.warnings?.length || 0,
    },
    quote: {
      symbol: p.token_y?.symbol,
      mint: p.token_y?.address,
    },
    pool_type: p.pool_type,
    bin_step: p.dlmm_params?.bin_step || null,
    fee_pct: p.fee_pct,

    // Core metrics (the numbers that matter)
    active_tvl: round(p.active_tvl),
    fee_window: round(p.fee),
    volume_window: round(p.volume),
    // API sometimes returns 0 for fee_active_tvl_ratio on short timeframes — compute from raw values as fallback
    fee_active_tvl_ratio: p.fee_active_tvl_ratio > 0
      ? fix(p.fee_active_tvl_ratio, 4)
      : (p.active_tvl > 0 ? fix((p.fee / p.active_tvl) * 100, 4) : 0),
    volatility: fix(p.volatility, 2),


    // Token health
    holders: p.base_token_holders,
    mcap: round(p.token_x?.market_cap),
    organic_score: Math.round(p.token_x?.organic_score || 0),
    token_age_hours: p.token_x?.created_at
      ? Math.floor((Date.now() - p.token_x.created_at) / 3_600_000)
      : null,
    dev: p.token_x?.dev || null,

    // Position health
    active_positions: p.active_positions,
    active_pct: fix(p.active_positions_pct, 1),
    open_positions: p.open_positions,
    discord_signal: Boolean(p.discord_signal),
    discord_signal_count: p.discord_signal_count || 0,
    discord_signal_seen_count: p.discord_signal_seen_count || 0,
    discord_signal_last_seen_at: p.discord_signal_last_seen_at || null,

    // Price action
    price: p.pool_price,
    price_change_pct: fix(p.pool_price_change_pct, 1),
    price_trend: p.price_trend,
    min_price: p.min_price,
    max_price: p.max_price,

    // Activity trends
    volume_change_pct: fix(p.volume_change_pct, 1),
    fee_change_pct: fix(p.fee_change_pct, 1),
    swap_count: p.swap_count,
    unique_traders: p.unique_traders,
  };
}

function round(n) {
  return n != null ? Math.round(n) : null;
}

function fix(n, decimals) {
  return n != null ? Number(n.toFixed(decimals)) : null;
}

function pushFilteredReason(list, pool, reason) {
  if (!list || !pool) return;
  list.push({
    name: pool.name || `${pool.base?.symbol || "?"}-${pool.quote?.symbol || "?"}`,
    reason,
  });
}
