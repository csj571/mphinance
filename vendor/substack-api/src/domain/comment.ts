import type { SubstackComment } from '@substack-api/internal'
import type { HttpClient } from '@substack-api/internal/http-client'
import type { CommentService } from '@substack-api/internal/services'

/**
 * Comment entity representing a comment on a post or note
 */
export class Comment {
  public readonly id: number
  public readonly body: string
  public readonly isAdmin?: boolean
  public readonly likesCount?: number

  constructor(
    private readonly rawData: SubstackComment,
    private readonly publicationClient: HttpClient,
    private readonly commentService: CommentService
  ) {
    this.id = rawData.id
    this.body = rawData.body
    this.isAdmin = rawData.author_is_admin
    this.likesCount = undefined // TODO: Extract from rawData when available
  }

  /**
   * Like this comment
   */
  async like(): Promise<void> {
    try {
      await this.commentService.likeComment(this.id)
    } catch (error) {
      throw new Error(`Failed to like comment ${this.id}: ${(error as Error).message}`)
    }
  }
}
