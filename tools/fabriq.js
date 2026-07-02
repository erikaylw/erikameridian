8/**
 * Fabriqtrade Portfolio PNL Tool
 * https://api.fabriqtrade.com/v1/portfolio/positions
 */

export async function getFabriqPnl({ wallet }) {
  if (!wallet) return { error: "wallet required" };
  
  try {
  const url = `https://api.fabriqtrade.com/v1/portfolio/positions?wallet=${wallet}&chain=solana`;
  
  const response = await fetch(url);
  if (!response.ok) {
    return { error: `Fabriq API error: ${response.status}` };
  }
  
