import config from "./screening.config.json";

export type AccountType = "social" | "promoter";

export interface SocialAccount {
  handle: string;
  followers: number;
  type: AccountType;
  mentions?: number;
  sentiment?: -1 | 0 | 1;
}

export interface ScreeningInput {
  category: string;
  path: string;
  summary?: string;
  tweetVolumeRecent: number;
  accounts: SocialAccount[];
  devTwitterOnGmgn?: string | null;
}

export type Narrative = "HIGH" | "MEDIUM" | "LOW";
export type Flag = "kol_shill" | "shiller_5k" | "major_kol" | "trending";
export type Sentiment = "bullish" | "bearish" | "neutral";

export interface ScreeningCard {
  narrative: Narrative;
  category: string;
  path: string;
  summary: string;
  signals: {
    tweet_volume_recent: number;
    kol_mentions_10k: number;
    social_accounts_5k: number;
    promoters_shillers_5k: number;
    major_kol_50k: number;
    sentiment: Sentiment;
    dev_twitter_gmgn: boolean;
  };
  flags: Flag[];
  top_social_accounts: Array<{ handle: string; followers: number; type: AccountType }>;
}

const t = config.thresholds;

function countAccounts(accounts: SocialAccount[], min: number, type?: AccountType) {
  return accounts.filter(
    (a) => a.followers >= min && (type === undefined || a.type === type)
  ).length;
}

function deriveSentiment(accounts: SocialAccount[]): Sentiment {
  const labelled = accounts.filter((a) => a.sentiment !== undefined);
  if (labelled.length === 0) return "neutral";
  const bullish = labelled.filter((a) => a.sentiment === 1).length;
  const bearish = labelled.filter((a) => a.sentiment === -1).length;
  if (bullish >= config.sentimentRules.bullish_kol_mentions_min && bullish > bearish)
    return "bullish";
  if (bearish / labelled.length >= config.sentimentRules.bearish_negative_ratio_min)
    return "bearish";
  return "neutral";
}

function deriveFlags(signals: ScreeningCard["signals"]): Flag[] {
  const r = config.flagRules;
  const flags: Flag[] = [];
  if (signals.promoters_shillers_5k >= r.kol_shill.promoters_5k_min) flags.push("kol_shill");
  if (signals.promoters_shillers_5k >= r.shiller_5k.promoters_5k_min) flags.push("shiller_5k");
  if (signals.major_kol_50k >= r.major_kol.major_kol_50k_min) flags.push("major_kol");
  if (signals.tweet_volume_recent >= r.trending.tweet_volume_recent_min) flags.push("trending");
  return flags;
}

function deriveNarrative(activeFlags: number, majorKol: number): Narrative {
  const r = config.narrativeRules;
  if (activeFlags >= r.HIGH.active_flags_min || majorKol >= r.HIGH.major_kol_50k_min)
    return "HIGH";
  if (activeFlags >= r.MEDIUM.active_flags_min || majorKol >= r.MEDIUM.major_kol_50k_min)
    return "MEDIUM";
  return "LOW";
}

export function screen(input: ScreeningInput): ScreeningCard {
  const signals: ScreeningCard["signals"] = {
    tweet_volume_recent: input.tweetVolumeRecent,
    kol_mentions_10k: countAccounts(input.accounts, t.kol_mention_min),
    social_accounts_5k: countAccounts(input.accounts, t.social_account_min, "social"),
    promoters_shillers_5k: countAccounts(input.accounts, t.promoter_min, "promoter"),
    major_kol_50k: countAccounts(input.accounts, t.major_kol_min),
    sentiment: deriveSentiment(input.accounts),
    dev_twitter_gmgn: !!input.devTwitterOnGmgn,
  };

  const flags = deriveFlags(signals);
  const narrative = deriveNarrative(flags.length, signals.major_kol_50k);

  const top_social_accounts = [...input.accounts]
    .sort((a, b) => b.followers - a.followers)
    .slice(0, 5)
    .map(({ handle, followers, type }) => ({ handle, followers, type }));

  return {
    narrative,
    category: input.category,
    path: input.path,
    summary:
      input.summary ??
      `${input.category} narrative — ${signals.major_kol_50k} major social account(s) 50k+`,
    signals,
    flags,
    top_social_accounts,
  };
}
