#!/usr/bin/env ts-node

/**
 * Summarize Recent Reads
 * 
 * Fetches the user's mixed content feed (posts, notes, chats) from the /reader/feed endpoint,
 * retrieves full text for posts, and compiles them into a daily digest with publication mapping.
 */

import { SubstackClient } from '../src/index'
import { config } from 'dotenv'
import * as fs from 'fs'
import * as path from 'path'
import { createInterface } from 'readline'

config()

interface PubInfo {
  name: string;
  url: string;
  id: number;
}

async function getCredentials(): Promise<{ token: string; publicationUrl: string }> {
  const envToken = process.env.SUBSTACK_API_KEY || process.env.SUBSTACK_SID || process.env.E2E_API_KEY
  const envHostname = process.env.SUBSTACK_HOSTNAME || process.env.E2E_HOSTNAME || 'substack.com'
  const envPublicationUrl = envHostname.startsWith('http') ? envHostname : `https://${envHostname}`

  if (envToken) {
    return { token: envToken, publicationUrl: envPublicationUrl }
  }

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout
  })

  return new Promise((resolve) => {
    rl.question('Enter your Substack API token: ', (token) => {
      rl.close()
      resolve({ token: token.trim(), publicationUrl: envPublicationUrl })
    })
  })
}

// Basic HTML stripper
function stripHtml(html: string): string {
  if (!html) return '';
  // Replace block elements with newlines
  let text = html.replace(/<\/(p|div|h[1-6]|li|tr)>/ig, '\n\n');
  text = text.replace(/<(br|hr)\s*\/?>/ig, '\n');
  // Remove all remaining tags
  text = text.replace(/<[^>]*>?/gm, '');
  // Decode common entities
  text = text.replace(/&nbsp;/g, ' ')
             .replace(/&amp;/g, '&')
             .replace(/&lt;/g, '<')
             .replace(/&gt;/g, '>')
             .replace(/&quot;/g, '"')
             .replace(/&#39;/g, "'");
  // Clean up extra whitespace
  return text.replace(/\n{3,}/g, '\n\n').trim();
}

async function runExample(): Promise<void> {
  console.log('🚀 Gathering recent reads from your feed...\n')

  try {
    const { token, publicationUrl } = await getCredentials()
    if (!token) throw new Error('API token is required')

    const client = new SubstackClient({ publicationUrl, token })
    const isConnected = await client.testConnectivity()
    
    if (!isConnected) {
      throw new Error('Failed to connect to Substack API')
    }

    // Load publication mapping
    const pubMap: Record<number, PubInfo> = {};
    try {
      const myReadsPath = path.join(process.cwd(), 'my-reads.json');
      if (fs.existsSync(myReadsPath)) {
        const reads: PubInfo[] = JSON.parse(fs.readFileSync(myReadsPath, 'utf-8'));
        for (const pub of reads) {
          pubMap[pub.id] = pub;
        }
        console.log(`Loaded ${Object.keys(pubMap).length} publication mappings from my-reads.json`);
      }
    } catch (e) {
      console.warn('Could not load my-reads.json, will use IDs only');
    }

    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - (24 * 60 * 60 * 1000));
    console.log(`Fetching feed items since ${oneDayAgo.toLocaleString()}\n`);

    const headers = {
      'Cookie': `substack.sid=${token}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    };

    let url = 'https://substack.com/api/v1/reader/feed';
    let hasMore = true;
    const recentPosts = [];
    const recentNotes = [];
    let stopCount = 0;

    while (hasMore) {
      const res = await fetch(url, { headers });
      if (res.status === 429) {
          console.log("Rate limited! Waiting 10 seconds...");
          await new Promise(r => setTimeout(r, 10000));
          continue;
      }
      
      const data = await res.json();
      const items = data.items || [];

      if (items.length === 0) break;

      for (const item of items) {
        let itemDate: Date | null = null;

        if (item.type === 'post' && item.post) {
          itemDate = new Date(item.post.post_date);
          if (itemDate < oneDayAgo) {
            stopCount++;
          } else {
            console.log(`[Post] "${item.post.title}" by ${item.publication?.name || 'Unknown'}`);
            recentPosts.push(item);
            stopCount = 0;
          }
        } else if (item.type === 'comment' && item.context?.type === 'note') {
          itemDate = new Date(item.context.timestamp);
          if (itemDate < oneDayAgo) {
            stopCount++;
          } else {
            const author = item.context.users?.[0]?.name || 'Unknown';
            console.log(`[Note] by ${author}: "${item.comment.body.substring(0, 50)}..."`);
            recentNotes.push(item);
            stopCount = 0;
          }
        }

        // The feed isn't strictly sorted by date, so we stop only after seeing several old items
        if (stopCount >= 10) {
          hasMore = false;
          break;
        }
      }

      if (hasMore && data.nextCursor) {
        url = `https://substack.com/api/v1/reader/feed?cursor=${encodeURIComponent(data.nextCursor)}`;
        // Brief delay between pages
        await new Promise(r => setTimeout(r, 500));
      } else {
        hasMore = false;
      }
    }

    console.log(`\nFound ${recentPosts.length} posts and ${recentNotes.length} notes. Processing content...`);
    
    let digest = `# Daily Substack Reads Digest\nGenerated: ${now.toLocaleString()}\n\n`;
    
    // Process Posts
    digest += `# 📰 Recent Posts\n\n`;
    for (let i = 0; i < recentPosts.length; i++) {
        const item = recentPosts[i];
        const p = item.post;
        const pub = item.publication;
        const pubName = pub?.name || pubMap[p.publication_id]?.name || 'Unknown';
        const pubUrl = pub?.base_url || pubMap[p.publication_id]?.url || '#';
        
        console.log(`Fetching [${i+1}/${recentPosts.length}]: ${p.title}`);
        
        try {
            const fullPost = await client.postForId(p.id);
            const cleanText = stripHtml(fullPost.htmlBody);
            const excerpt = cleanText.substring(0, 2000) + (cleanText.length > 2000 ? '...\n(truncated)' : '');
            
            digest += `## [${p.title}](${p.canonical_url})\n`;
            digest += `**By:** [${pubName}](${pubUrl}) · **Date:** ${new Date(p.post_date).toLocaleString()}\n\n`;
            digest += `> 💬 _[Agent: write a one-liner in Michael's voice after reading]_ \n\n`;
            digest += `${excerpt}\n\n`;
            digest += `---\n\n`;
            
            await new Promise(resolve => setTimeout(resolve, 300));
        } catch (e) {
            console.error(`  -> Failed to fetch full post: ${(e as Error).message}`);
            // Fallback for failed full fetch
            digest += `## [${p.title}](${p.canonical_url})\n`;
            digest += `**By:** [${pubName}](${pubUrl}) · **Date:** ${new Date(p.post_date).toLocaleString()}\n\n`;
            digest += `> 💬 _[Agent: write a one-liner in Michael's voice]_ \n\n`;
            digest += `${p.description || 'Full content unavailable.'}\n\n`;
            digest += `---\n\n`;
        }
    }

    // Process Notes
    if (recentNotes.length > 0) {
      digest += `# 📝 Notes from the Feed\n\n`;
      for (const item of recentNotes) {
        const author = item.context.users?.[0]?.name || 'Unknown';
        const handle = item.context.users?.[0]?.handle || 'unknown';
        const date = new Date(item.context.timestamp).toLocaleString();
        
        digest += `### @${handle} (${author})\n`;
        digest += `> ${item.comment.body}\n`;
        digest += `*${date}*\n\n`;
        digest += `---\n\n`;
      }
    }

    const outputPath = path.join(process.cwd(), 'daily-reads-digest.md');
    fs.writeFileSync(outputPath, digest);
    console.log(`\n✅ Saved daily digest to ${outputPath}`);
    console.log('Voice check: I will now help you fill in those placeholders!');

  } catch (error) {
    console.error('\n❌ Error:', (error as Error).message)
    process.exit(1)
  }
}

if (require.main === module) {
  runExample().catch(console.error)
}

export { runExample }

