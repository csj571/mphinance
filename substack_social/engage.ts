import { SubstackClient } from 'substack-api';
import * as fs from 'fs';

const sid = "s%3AbOEIouthsRC1PWBVi8Jl07qP4-pMjLiz.8aqscWSVtI65wqmEAsGMfJpWSxHXyaIJgcYadK%2BoG7k";

async function run() {
  const client = new SubstackClient({
    token: sid,
    publicationUrl: 'mphinance.substack.com',
  });

  const isConnected = await client.testConnectivity();
  if (!isConnected) {
    console.error("Not connected! SID might be expired.");
    return;
  }
  
  let me;
  try {
     me = await client.ownProfile();
     console.log(`Authenticated as ${me.name}`);
  } catch (e) {
     console.error("Failed to get own profile:", e.message);
     return;
  }
  
  const following = [];
  try {
     for await (const user of me.following({ limit: 100 })) {
        following.push(user);
     }
  } catch (e) {
     console.error("Failed getting following:", e.message);
  }
  
  console.log(`Found ${following.length} followed profiles.`);
  
  const twoWeeksAgo = new Date();
  twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
  
  const items: any[] = [];
  let likedCount = 0;
  let attempts = 0;
  
  for (const prof of following) {
     console.log(`Checking @${prof.slug}`);
     try {
       for await (const post of prof.posts({ limit: 10 })) {
         if (post.publishedAt && post.publishedAt > twoWeeksAgo) {
            attempts++;
            let liked = false;
            try {
              if (likedCount < 200) {
                 await post.like();
                 likedCount++;
                 liked = true;
              }
            } catch(e: any) { console.error(`Like Post failed: ${e.message}`); }
            
            let url = "";
            try {
               const fp = await post.fullPost();
               url = fp.url;
            } catch(e) {
               url = `https://${prof.slug}.substack.com/p/${post.id}`;
            }

            items.push({
               type: 'Post',
               author: prof.name,
               title: post.title || 'Untitled',
               url: url,
               snippet: post.truncatedBody || post.body || "",
               date: post.publishedAt,
               liked
            });
         }
       }
       
       for await (const note of prof.notes({ limit: 20 })) {
         // Some type mappings use createdAt for notes
         const noteDate = (note as any).createdAt || (note as any).publishedAt;
         if (noteDate && new Date(noteDate) > twoWeeksAgo) {
            attempts++;
            let liked = false;
            try {
              if (likedCount < 200) {
                 await note.like();
                 likedCount++;
                 liked = true;
              }
            } catch(e: any) { console.error(`Like Note failed: ${e.message}`); }
            
            items.push({
               type: 'Note',
               author: prof.name,
               title: 'Note',
               url: `https://substack.com/profile/${prof.id}/note/${note.id}`,
               snippet: note.body || "",
               date: new Date(noteDate),
               liked
            });
         }
       }
     } catch(e: any) {
         console.error(`Error processing @${prof.slug}: ${e.message}`);
     }
     
     if (likedCount >= 200) {
       console.log("Reached 200 likes. Stopping early.");
       break;
     }
  }
  
  items.sort((a, b) => b.date.getTime() - a.date.getTime());
  
  let md = `# Your Substack Catch-Up (Last 2 Weeks)\n\n`;
  md += `*Processed ${attempts} items, successfully liked ${likedCount} recent posts across your network.*\n\n`;
  for (const item of items) {
    const status = item.liked ? "❤️ Liked" : "📝 Read";
    md += `### [${item.type}] ${item.title} by ${item.author} (${status})\n`;
    md += `*${item.date.toISOString().split('T')[0]}* — [Read Here](${item.url})\n\n`;
    const snippet = typeof item.snippet === 'string' ? item.snippet.replace(/\n/g, '\n> ') : '';
    md += `> ${snippet.substring(0, 300)}...\n\n`;
    md += `---\n\n`;
  }
  
  const path = "/home/mph/.gemini/antigravity/brain/09965367-b7d3-42a0-94cf-f9897122b399/artifacts/substack_reading_list.md";
  fs.mkdirSync("/home/mph/.gemini/antigravity/brain/09965367-b7d3-42a0-94cf-f9897122b399/artifacts", { recursive: true });
  fs.writeFileSync(path, md);
  console.log(`Reading list written to ${path}`);
  console.log(`Total attempts: ${attempts}, total liked: ${likedCount}`);
}

run().catch(console.error);
