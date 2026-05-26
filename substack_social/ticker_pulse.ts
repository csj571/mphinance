import { SubstackClient } from 'substack-api';
import * as fs from 'fs';
import * as path from 'path';

const sid = process.env.SUBSTACK_SID;
if (!sid) {
  console.error("SUBSTACK_SID not set. Export it (Windows: User-scope env var) and re-run.");
  process.exit(1);
}

// ─── EDIT THIS LIST ────────────────────────────────────────────────────────
// Curated finance / equity-analysis Substacks. Slug = the subdomain
// (e.g. `yetanothervalueblog` for yetanothervalueblog.substack.com, or
// `thebearcave` for thebearcave.substack.com). Add/remove freely.
// Cashtag-mode only catches `$TICKER` — pubs that don't write tickers
// that way (pure macro, pure narrative) will show zero hits, which is fine.
// ───────────────────────────────────────────────────────────────────────────
const PUBLICATIONS = [
  'yetanothervalueblog',   // Andrew Walker — deep value, ticker-heavy
  'thebearcave',           // Edwin Dorsey — short reports
  'nongaap',               // NonGAAP — earnings teardowns
  'moontower',             // Kris Abdelmessih — options / equity
  'compound248',           // David Marino-Nachison
  'netinterest',           // Marc Rubinstein — banks / financials
  'thediff',               // Byrne Hobart — strategy
  'doomberg',              // energy + macro
  'apricitas',             // Joey Politano — macro
  'calculatedrisk',        // Bill McBride
  'youngmoney',            // Jack Raines
  'thelastbearstanding',
  'concoda',
  'heisenbergreport',
];

const LOOKBACK_DAYS = 7;
const MAX_POSTS_PER_PUB = 15;

// Filter out non-equity cashtags that show up a lot (currencies, etc.)
const IGNORE_TICKERS = new Set([
  'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD', 'AUD',
  'US', 'UK', 'EU', 'USA',
]);

// Cashtag regex: `$` then 1-5 uppercase letters, word boundary after.
// Allows optional `.` for class shares (e.g. $BRK.B) — captured separately.
const CASHTAG_RE = /\$([A-Z]{1,5})(?:\.([A-Z]))?\b/g;

interface PostHit {
  title: string;
  url: string;
  author: string;
  publishedAt: Date;
  mentions: number;
}

interface TickerStat {
  ticker: string;
  totalMentions: number;
  posts: PostHit[];
}

function stripHtml(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ');
}

function extractCashtags(text: string): Map<string, number> {
  const counts = new Map<string, number>();
  for (const match of text.matchAll(CASHTAG_RE)) {
    const base = match[1];
    const cls = match[2];
    const ticker = cls ? `${base}.${cls}` : base;
    if (IGNORE_TICKERS.has(base)) continue;
    counts.set(ticker, (counts.get(ticker) || 0) + 1);
  }
  return counts;
}

async function run() {
  const client = new SubstackClient({
    token: sid,
    publicationUrl: 'mphinance.substack.com',
  });

  if (!(await client.testConnectivity())) {
    console.error("Not connected. SID expired?");
    return;
  }

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - LOOKBACK_DAYS);

  const tickerStats = new Map<string, TickerStat>();
  let postsScanned = 0;
  let pubsHit = 0;

  for (const slug of PUBLICATIONS) {
    let prof;
    try {
      prof = await client.profileForSlug(slug);
    } catch (e: any) {
      console.error(`✗ ${slug}: ${e.message}`);
      continue;
    }
    pubsHit++;
    console.log(`→ scanning @${slug}`);

    let postsThisPub = 0;
    try {
      for await (const post of prof.posts({ limit: MAX_POSTS_PER_PUB })) {
        if (!post.publishedAt || post.publishedAt < cutoff) continue;

        let bodyHtml = '';
        let url = '';
        try {
          const fp = await post.fullPost();
          bodyHtml = fp.htmlBody || fp.body || '';
          url = fp.url;
        } catch (e: any) {
          console.error(`  ! fullPost(${post.id}) failed: ${e.message}`);
          continue;
        }

        const haystack = `${post.title || ''} ${post.subtitle || ''} ${stripHtml(bodyHtml)}`;
        const cashtags = extractCashtags(haystack);
        if (cashtags.size === 0) continue;

        postsScanned++;
        postsThisPub++;
        for (const [ticker, count] of cashtags) {
          if (!tickerStats.has(ticker)) {
            tickerStats.set(ticker, { ticker, totalMentions: 0, posts: [] });
          }
          const stat = tickerStats.get(ticker)!;
          stat.totalMentions += count;
          stat.posts.push({
            title: post.title || 'Untitled',
            url,
            author: slug,
            publishedAt: post.publishedAt,
            mentions: count,
          });
        }
      }
    } catch (e: any) {
      console.error(`  ! posts(@${slug}) failed: ${e.message}`);
    }
    console.log(`  posts w/ cashtags: ${postsThisPub}`);
  }

  // Sort by total mentions desc, then by distinct-post-count desc.
  const ranked = [...tickerStats.values()].sort((a, b) => {
    if (b.totalMentions !== a.totalMentions) return b.totalMentions - a.totalMentions;
    return b.posts.length - a.posts.length;
  });

  const today = new Date().toISOString().split('T')[0];
  let md = `# Finance Substack Ticker Pulse — ${today}\n\n`;
  md += `*Lookback: ${LOOKBACK_DAYS} days · Publications scanned: ${pubsHit}/${PUBLICATIONS.length} · Posts w/ cashtags: ${postsScanned} · Distinct tickers: ${ranked.length}*\n\n`;

  md += `## Leaderboard\n\n`;
  md += `| Rank | Ticker | Mentions | Posts |\n`;
  md += `|-----:|:-------|---------:|------:|\n`;
  ranked.slice(0, 30).forEach((s, i) => {
    md += `| ${i + 1} | \`$${s.ticker}\` | ${s.totalMentions} | ${s.posts.length} |\n`;
  });

  md += `\n## Top mentions — detail\n\n`;
  for (const stat of ranked.slice(0, 15)) {
    md += `### $${stat.ticker} — ${stat.totalMentions} mentions across ${stat.posts.length} post(s)\n\n`;
    const topPosts = [...stat.posts]
      .sort((a, b) => b.mentions - a.mentions)
      .slice(0, 3);
    for (const p of topPosts) {
      const date = p.publishedAt.toISOString().split('T')[0];
      md += `- [${p.title}](${p.url}) — @${p.author} · ${date} · ${p.mentions} mention(s)\n`;
    }
    md += `\n`;
  }

  const outDir = path.join(__dirname, 'data');
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, `ticker_pulse_${today}.md`);
  fs.writeFileSync(outPath, md);
  console.log(`\n✓ Wrote ${outPath}`);
  console.log(`  ${ranked.length} distinct tickers across ${postsScanned} posts.`);
}

run().catch(console.error);
