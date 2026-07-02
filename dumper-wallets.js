/**
 * Dumper Wallets — known dumping/bundler wallets to check during screening.
 *
 * When screening a pool, the system checks if any of these wallets are
 * in the top holders of the candidate token. If yes, the pool is flagged/dropped.
 */

import fs from "fs";
import { log } from "./logger.js";

const DUMPER_FILE = "./dumper-wallets.json";

function load() {
  if (!fs.existsSync(DUMPER_FILE)) return { wallets: [] };
  try {
    return JSON.parse(fs.readFileSync(DUMPER_FILE, "utf8"));
  } catch {
    return { wallets: [] };
  }
}

/**
 * Returns the full list of dumper wallet addresses.
 */
export function getDumperAddresses() {
  return load().wallets.map((w) => w.address);
}

/**
 * Check if any dumper wallets are in the top holders of a token.
 * @param {Array} holders — array of holder objects from getTokenHolders()
 * @returns {{ found: boolean, matches: Array }}
 */
export function checkDumpersInHolders(holders) {
  if (!holders || holders.length === 0) {
    return { found: false, matches: [] };
  }

  const dumperAddresses = getDumperAddresses();
  if (dumperAddresses.length === 0) {
    return { found: false, matches: [] };
  }

  const dumperSet = new Set(dumperAddresses.map((a) => a.toLowerCase()));
  const matches = holders.filter((h) => {
    const addr = (h.address || h.owner || "").toLowerCase();
    const accAddr = (h.account_address || "").toLowerCase();
    return dumperSet.has(addr) || dumperSet.has(accAddr);
  });

  return {
    found: matches.length > 0,
    matches: matches.map((m) => ({
      address: m.address || m.owner,
      balance_pct: m.amount_percentage || m.pct,
      tag: m.tags?.join(",") || "",
    })),
  };
}

/**
 * Add a dumper wallet to the list.
 */
export function addDumperWallet({ address, tag, reason }) {
  if (!address) return { error: "address required" };

  const data = load();
  const exists = data.wallets.find(
    (w) => w.address.toLowerCase() === address.toLowerCase()
  );
  if (exists) {
    return { already_exists: true, address };
  }

  data.wallets.push({
    address,
    tag: tag || "unknown",
    reason: reason || "no reason",
    added_at: new Date().toISOString(),
  });

  fs.writeFileSync(DUMPER_FILE, JSON.stringify(data, null, 2));
  log("dumper_wallets", `Added dumper wallet: ${address} (${tag})`);
  return { added: true, address, tag, reason };
}
