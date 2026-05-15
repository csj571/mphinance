import { SubstackClient } from '../src/index'
import { config } from 'dotenv'

config()

async function main() {
  const token = process.env.SUBSTACK_SID
  if (!token) {
    console.error('SUBSTACK_SID not found in environment')
    process.exit(1)
  }

  const client = new SubstackClient({ token, publicationUrl: 'https://mphinance.substack.com' })
  const me = await client.ownProfile()

  console.log(`\n📊 Analytics for ${me.name} (@${me.handle})\n`)

  console.log('📰 RECENT POSTS')
  console.log('----------------')
  for await (const post of me.posts({ limit: 5 })) {
    console.log(`Title: ${post.title}`)
    console.log(`Date:  ${post.publishedAt.toLocaleDateString()}`)
    console.log(`Likes: ${post.likesCount} | Comments: ${post.commentCount} | Restacks: ${post.restacksCount}`)
    if (post.reactions) {
        const reactions = Object.entries(post.reactions)
            .map(([emoji, count]) => `${emoji} ${count}`)
            .join(' ')
        console.log(`Reactions: ${reactions}`)
    }
    console.log(`URL:   ${post.url || 'N/A'}`)
    console.log('')
  }

  console.log('📝 RECENT NOTES')
  console.log('----------------')
  for await (const note of me.notes({ limit: 5 })) {
    const text = note.body.substring(0, 80).replace(/\n/g, ' ')
    console.log(`Content: ${text}...`)
    console.log(`Likes:   ${note.likesCount}`)
    console.log('')
  }
}

main().catch(err => {
    console.error('\n❌ Analytics failed:');
    console.error(err);
    process.exit(1);
})
