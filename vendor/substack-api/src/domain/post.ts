import type { SubstackFullPost, SubstackPreviewPost } from '@substack-api/internal'
import type { HttpClient } from '@substack-api/internal/http-client'
import type { CommentService, PostService } from '@substack-api/internal/services'
import { Comment } from '@substack-api/domain/comment'

/**
 * Post interface defining the common contract for all post types
 */
export interface Post {
  readonly id: number
  readonly title: string
  readonly subtitle: string
  readonly body: string
  readonly truncatedBody: string
  readonly likesCount: number
  readonly author: {
    id: number
    name: string
    handle: string
    avatarUrl: string
  }
  readonly publishedAt: Date

  comments(options?: { limit?: number }): AsyncIterable<Comment>
  like(): Promise<void>
  addComment(data: { body: string }): Promise<Comment>
}

/**
 * PreviewPost entity representing a Substack post with truncated content
 */
export class PreviewPost implements Post {
  public readonly id: number
  public readonly title: string
  public readonly subtitle: string
  public readonly body: string
  public readonly truncatedBody: string
  public readonly likesCount: number
  public readonly author: {
    id: number
    name: string
    handle: string
    avatarUrl: string
  }
  public readonly commentCount: number
  public readonly restacksCount: number
  public readonly reactions?: Record<string, number>
  public readonly publishedAt: Date
  public readonly url: string

  constructor(
    rawData: SubstackPreviewPost,
    private readonly publicationClient: HttpClient,
    private readonly commentService: CommentService,
    private readonly postService: PostService
  ) {
    this.id = rawData.id
    this.title = rawData.title || 'Untitled'
    this.subtitle = rawData.subtitle || ''
    this.truncatedBody = rawData.truncated_body_text || ''
    this.body = rawData.truncated_body_text || ''
    this.likesCount = rawData.reaction_count || 0
    this.commentCount = rawData.comment_count || 0
    this.restacksCount = rawData.restacks_count || 0
    this.reactions = rawData.reactions
    this.publishedAt = rawData.post_date ? new Date(rawData.post_date) : new Date()
    this.url = rawData.canonical_url || ''

    // TODO: Extract author information from rawData
    // For now, use placeholder values
    this.author = {
      id: 0,
      name: 'Unknown Author',
      handle: 'unknown',
      avatarUrl: ''
    }
  }

  /**
   * Fetch the full post data with HTML body content
   * @returns Promise<FullPost> - A FullPost instance with complete content
   * @throws {Error} When full post retrieval fails
   */
  async fullPost(): Promise<FullPost> {
    try {
      const fullPostData = await this.postService.getPostById(this.id)
      return new FullPost(fullPostData, this.publicationClient, this.commentService, this.postService)
    } catch (error) {
      throw new Error(`Failed to fetch full post ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Get comments for this post
   * @throws {Error} When comment retrieval fails or API is unavailable
   */
  async *comments(options: { limit?: number } = {}): AsyncIterable<Comment> {
    try {
      const commentsData = await this.commentService.getCommentsForPost(this.id)

      let count = 0
      for (const commentData of commentsData) {
        if (options.limit && count >= options.limit) break
        yield new Comment(commentData, this.publicationClient, this.commentService)
        count++
      }
    } catch (error) {
      throw new Error(`Failed to get comments for post ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Like this post
   */
  async like(): Promise<void> {
    try {
      await this.postService.likePost(this.id)
    } catch (error) {
      throw new Error(`Failed to like post ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Add a comment to this post
   */
  async addComment(data: { body: string }): Promise<Comment> {
    try {
      const commentData = await this.commentService.createComment(this.id, data.body)
      return new Comment(commentData, this.publicationClient, this.commentService)
    } catch (error) {
      throw new Error(`Failed to add comment to post ${this.id}: ${(error as Error).message}`)
    }
  }
}

/**
 * FullPost entity representing a Substack post with complete HTML content
 */
export class FullPost implements Post {
  public readonly id: number
  public readonly title: string
  public readonly subtitle: string
  public readonly body: string
  public readonly truncatedBody: string
  public readonly likesCount: number
  public readonly author: {
    id: number
    name: string
    handle: string
    avatarUrl: string
  }
  public readonly publishedAt: Date
  public readonly url: string
  public readonly htmlBody: string
  public readonly slug: string
  public readonly createdAt: Date
  public readonly reactions?: Record<string, number>
  public readonly restacks?: number
  public readonly postTags?: string[]
  public readonly coverImage?: string
  public readonly commentCount: number
  public readonly restacksCount: number

  constructor(
    rawData: SubstackFullPost,
    private readonly publicationClient: HttpClient,
    private readonly commentService: CommentService,
    private readonly postService: PostService
  ) {
    this.id = rawData.id
    this.title = rawData.title
    this.subtitle = rawData.subtitle || ''
    this.truncatedBody = rawData.truncated_body_text || ''
    this.body = rawData.body_html || rawData.htmlBody || rawData.truncated_body_text || ''
    this.likesCount = rawData.reaction_count || 0
    this.commentCount = rawData.comment_count || 0
    this.restacksCount = rawData.restacks_count || rawData.restacks || 0
    this.publishedAt = new Date(rawData.post_date)
    this.url = rawData.canonical_url || ''

    // TODO: Extract author information from rawData
    // For now, use placeholder values
    this.author = {
      id: 0,
      name: 'Unknown Author',
      handle: 'unknown',
      avatarUrl: ''
    }

    // Prefer body_html from the full post response, fall back to htmlBody for backward compatibility
    this.htmlBody = rawData.body_html || rawData.htmlBody || ''
    this.slug = rawData.slug
    this.createdAt = new Date(rawData.post_date)
    this.reactions = rawData.reactions
    this.restacks = rawData.restacks
    this.postTags = rawData.postTags
    this.coverImage = rawData.cover_image || undefined
  }

  /**
   * Get comments for this post
   * @throws {Error} When comment retrieval fails or API is unavailable
   */
  async *comments(options: { limit?: number } = {}): AsyncIterable<Comment> {
    try {
      const commentsData = await this.commentService.getCommentsForPost(this.id)

      let count = 0
      for (const commentData of commentsData) {
        if (options.limit && count >= options.limit) break
        yield new Comment(commentData, this.publicationClient, this.commentService)
        count++
      }
    } catch (error) {
      throw new Error(`Failed to get comments for post ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Like this post
   */
  async like(): Promise<void> {
    try {
      await this.postService.likePost(this.id)
    } catch (error) {
      throw new Error(`Failed to like post ${this.id}: ${(error as Error).message}`)
    }
  }

  /**
   * Add a comment to this post
   */
  async addComment(data: { body: string }): Promise<Comment> {
    try {
      const commentData = await this.commentService.createComment(this.id, data.body)
      return new Comment(commentData, this.publicationClient, this.commentService)
    } catch (error) {
      throw new Error(`Failed to add comment to post ${this.id}: ${(error as Error).message}`)
    }
  }
}
