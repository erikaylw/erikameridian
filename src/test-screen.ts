import { screen } from "./screening";

const card = screen({
  category: "charity_donation",
  path: "ca_search",
  tweetVolumeRecent: 40,
  accounts: [
    { handle: "@Pumpfun",          followers: 651400, type: "social",   sentiment: 1 },
    { handle: "@whalewatchalert",  followers: 184600, type: "social",   sentiment: 1 },
    { handle: "@soltrader_01",     followers:  61200, type: "promoter", sentiment: 1 },
    { handle: "@badattrading_",    followers:  48200, type: "social",   sentiment: 1 },
    { handle: "@Humanevolvd",      followers:  25000, type: "promoter" },
  ],
  devTwitterOnGmgn: null,
});

console.log(JSON.stringify(card, null, 2));
