import type { SubstackNote } from '@substack-api/internal'
import type { HttpClient } from '@substack-api/internal/http-client'
import { Comment } from '@substack-api/domain/comment'
import type { CommentService } from '@substack-api/internal/services'

/**
 * Note entity representing a Substack note
 */
export class Note {
  public readonly id: string
  public readonly body: string
  public readonly likesCount: number
  public readonly author: {
    id: number
    name: string
    handle: string
    avatarUrl: string
  }
  public readonly publishedAt: Date

  constructor(
    private readonly rawData: SubstackNote,
    private readonly publicationClient: HttpClient,
    private readonly commentService: CommentService
  ) {
    this.id = rawData.entity_key
    this.body = rawData.comment?.body || ''
    this.likesCount = rawData.comment?.reaction_count || 0
    this.publishedAt = new Date(rawData.context.timestamp)

    // Extract author info from context users
    const firstUser = rawData.context.users[0]
    this.author = {
      id: firstUser?.id || 0,
      name: firstUser?.name || 'Unknown',
      handle: firstUser?.handle || 'unknown',
      avatarUrl: firstUser?.photo_url || ''
    }
  }

  /**
   * Get parent comments for this note
   */
  async *comments(): AsyncIterable<Comment> {
    // Convert parent comments to Comment entities
    for (const parentComment of this.rawData.parentComments || []) {
      if (parentComment) {
        // Convert note comment format to SubstackComment format - minimal fields only
        const commentData = {
          id: parentComment.id,
          body: parentComment.body,
          author_is_admin: false // Not available in note comment format
        }
        yield new Comment(commentData, this.publicationClient, this.commentService)
      }
    }
  }

  /**
   * Like this note
   */
  async like(): Promise<void> {
    try {
      await this.commentService.likeComment(Number(this.id))
    } catch (error) {
      throw new Error(`Failed to like note ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Add a comment to this note
   */
  async addComment(text: string): Promise<Comment> {
    try {
      // For notes, the "post_id" is actually null and we reply to the comment
      // Substack API for replying to a note is often POST /api/v1/comment/<id>/reply
      // But for now let's stick to what we know or wait for more research.
      // Actually, many "notes" are just comments with a specific surface.
      throw new Error('Note commenting not yet fully implemented - requires reply API')
    } catch (error) {
      throw new Error(`Failed to add comment to note ${this.id}: ${(error as Error).message}`)
    }
  }
}
