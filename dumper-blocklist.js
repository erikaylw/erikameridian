/**
 * Dumper blocklist — wallet addresses that should never be deployed into.
 *
 * The bot checks top holders of candidate tokens before deploying.
 * If any blocked dumper wallet appears in the top 20 holders with ≥ 0.5%,
 * the deploy is blocked with a clear reason.
 *
 * Agent/user can block dumper wallets via Telegram ("blacklist this dumper").
 */

import fs from "fs";
import { log } from "./logger.js";

const BLOCKLIST_FILE = "./dumper-blocklist.json";

function load() {
  if (!fs.existsSync(BLOCKLIST_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(BLOCKLIST_FILE, "utf8"));
  } catch {
    return {};
  }
}

function save(data) {
  fs.writeFileSync(BLOCKLIST_FILE, JSON.stringify(data, null, 2));
}

// ─── Check ─────────────────────────────────────────────────────

/**
 * Returns true if the wallet is on the dumper blocklist.
 */
export function isDumperBlocked(wallet) {
  if (!wallet) return false;
  return !!load()[wallet];
}

/**
 * Returns the full blocklist database.
 */
export function getBlockedDumpers() {
  return load();
}

/**
 * Check a list of holder addresses against the dumper blocklist.
 * Returns matched entries with their holding percentage.
 */
export function checkHoldersAgainstDumperBlocklist(holders) {
  if (!Array.isArray(holders) || holders.length === 0) return [];
  const db = load();
  if (Object.keys(db).length === 0) return [];

  return holders
    .filter((h) => h?.address && db[h.address])
    .map((h) => ({
      address: h.address,
      label: db[h.address].label,
      reason: db[h.address].reason,
      pct: h.pct,
      amount: h.amount,
    }));
}

// ─── Tool Handlers ─────────────────────────────────────────────

/**
 * Tool handler: block_dumper
 */
export function blockDumper({ wallet, label, reason }) {
  if (!wallet) return { error: "wallet required" };

  const db = load();

  if (db[wallet]) {
    return {
      already_blocked: true,
      wallet,
      label: db[wallet].label,
      reason: db[wallet].reason,
    };
  }

  db[wallet] = {
    label: label || "unknown",
    reason: reason || "no reason provided",
    added_at: new Date().toISOString(),
  };

  save(db);
  log("dumper_blocklist", `Blocked dumper ${label || wallet}: ${reason}`);
  return { blocked: true, wallet, label, reason };
}

/**
 * Tool handler: unblock_dumper
 */
export function unblockDumper({ wallet }) {
  if (!wallet) return { error: "wallet required" };

  const db = load();

  if (!db[wallet]) {
    return { error: `Wallet ${wallet} not found on dumper blocklist` };
  }

  const entry = db[wallet];
  delete db[wallet];
  save(db);
  log("dumper_blocklist", `Removed dumper ${entry.label || wallet} from blocklist`);
  return { unblocked: true, wallet, was: entry };
}

/**
 * Tool handler: list_blocked_dumpers
 */
export function listBlockedDumpers() {
  const db = load();
  const entries = Object.entries(db).map(([wallet, info]) => ({ wallet, ...info }));

  return {
    count: entries.length,
    blocked_dumpers: entries,
  };
}
