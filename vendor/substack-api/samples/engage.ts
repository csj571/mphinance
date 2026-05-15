#!/usr/bin/env ts-node

/**
 * Substack Engagement Dashboard
 *
 * READ-ONLY. This script NEVER posts, comments, or likes anything.
 *
 * SAFETY RULES (non-negotiable):
 *   1. NO automated posting of Notes or Posts — ever.
 *   2. NO automated comments — suggested replies are for copy-paste ONLY.
 *   3. NO liking without explicit user action.
 *   4. Replies are limited to ONE sentence matching Michael's voice (VOICE.md).
 *   5. This script only reads data. It prints. That's it.
 *
 * To actually reply to a comment, copy the suggested text and paste it manually
 * on Substack. The agent will NEVER hit a write endpoint from this script.
 */

import { SubstackClient } from '../src/index'
import { config } from 'dotenv'

config()

// ============================================================
// SAFETY BANNER — printed every run so there's no confusion
// ============================================================
console.log('╔══════════════════════════════════════════════╗')
console.log('║  ENGAGEMENT DASHBOARD  —  READ-ONLY MODE     ║')
console.log('║  No posts. No comments. No likes. Ever.      ║')
console.log('║  Copy-paste replies manually on Substack.    ║')
console.log('╚══════════════════════════════════════════════╝')
console.log('')

async function getCredentials(): Promise<{ token: string; publicationUrl: string }> {
  const envToken = process.env.SUBSTACK_API_KEY || process.env.SUBSTACK_SID || process.env.E2E_API_KEY
  const envHostname = process.env.SUBSTACK_HOSTNAME || process.env.E2E_HOSTNAME || 'mphinance.substack.com'
  const envPublicationUrl = envHostname.startsWith('http') ? envHostname : `https://${envHostname}`

  if (!envToken) {
    throw new Error('SUBSTACK_SID environment variable is required')
  }

  return { token: envToken, publicationUrl: envPublicationUrl }
}

async function runEngage(): Promise<void> {
  console.log('🔍 Fetching recent comments for engagement...\n')

  try {
    const { token, publicationUrl } = await getCredentials()
    const client = new SubstackClient({ publicationUrl, token })
    
    const isConnected = await client.testConnectivity()
    if (!isConnected) {
      throw new Error('Failed to connect to Substack API')
    }

    const myProfile = await client.ownProfile()
    console.log(`Authenticated as: ${myProfile.name}\n`)

    const recentPosts = []
    for await (const post of myProfile.posts({ limit: 5 })) {
      recentPosts.push(post)
    }

    console.log(`Checking comments on ${recentPosts.length} most recent posts...\n`)

    for (const post of recentPosts) {
      console.log(`--- POST: ${post.title} ---`)
      console.log(`URL: ${post.url || 'N/A'}`)
      
      let foundComments = false
      for await (const comment of post.comments({ limit: 20 })) {
        // Only look at non-admin comments (Michael's replies are admin)
        if (comment.isAdmin) continue

        foundComments = true
        console.log(`\n💬 COMMENT ID ${comment.id}:`)
        console.log(`   "${comment.body}"`)
        console.log(`\n✨ SUGGESTED REPLY (Michael's Voice):`)
        console.log(`   [Agent: generate a sarcastic, data-driven, one-sentence reply here]`)
        console.log(`   ----------------------------------------------------------`)
      }

      if (!foundComments) {
        console.log('   (No recent comments to engage with)')
      }
      console.log('\n')
    }

    console.log('✅ Engagement report complete.')
    console.log('NOTE: I will now help you generate those suggested replies in the chat.')

  } catch (error) {
    console.error('\n❌ Error:', (error as Error).message)
    process.exit(1)
  }
}

if (require.main === module) {
  runEngage().catch(console.error)
}

export { runEngage }
