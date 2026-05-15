import * as t from 'io-ts'

/**
 * Raw API response shape for full posts from /posts/by-id/:id endpoint
 * Only validates fields actually used by FullPost domain class
 */
export const SubstackFullPostCodec = t.intersection([
  t.type({
    id: t.number,
    title: t.string,
    slug: t.string,
    post_date: t.string,
    canonical_url: t.string
  }),
  t.partial({
    subtitle: t.union([t.string, t.null]),
    truncated_body_text: t.string,
    body_html: t.union([t.string, t.null]),
    htmlBody: t.union([t.string, t.null]),
    reactions: t.record(t.string, t.number),
    restacks: t.number,
    reaction_count: t.number,
    comment_count: t.number,
    restacks_count: t.number,
    postTags: t.array(t.any),
    cover_image: t.union([t.string, t.null])
  })
])

export type SubstackFullPost = t.TypeOf<typeof SubstackFullPostCodec>
