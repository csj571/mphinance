import type { HttpClient } from '@substack-api/internal/http-client'
import type { SubstackComment } from '@substack-api/internal/types'
import { SubstackCommentCodec, SubstackCommentResponseCodec } from '@substack-api/internal/types'
import { decodeOrThrow } from '@substack-api/internal/validation'

/**
 * Service responsible for comment-related HTTP operations
 * Returns internal types that can be transformed into domain models
 */
export class CommentService {
  constructor(private readonly publicationClient: HttpClient) {}

  /**
   * Get comments for a post
   * @param postId - The post ID
   * @returns Promise<SubstackComment[]> - Raw comment data from API (validated)
   * @throws {Error} When comments cannot be retrieved or validation fails
   */
  async getCommentsForPost(postId: number): Promise<SubstackComment[]> {
    const response = await this.publicationClient.get<{ comments?: unknown[] }>(
      `/post/${postId}/comments`
    )

    const comments = response.comments || []

    // Validate each comment with io-ts
    return comments.map((comment, index) =>
      decodeOrThrow(SubstackCommentCodec, comment, `Comment ${index} in post response`)
    )
  }

  /**
   * Get a specific comment by ID
   * @param id - The comment ID
   * @returns Promise<SubstackComment> - Raw comment data from API (validated)
   * @throws {Error} When comment is not found, API request fails, or validation fails
   */
  async getCommentById(id: number): Promise<SubstackComment> {
    const rawResponse = await this.publicationClient.get<unknown>(`/reader/comment/${id}`)

    // Validate the response structure with io-ts
    const response = decodeOrThrow(SubstackCommentResponseCodec, rawResponse, 'Comment response')

    // Transform the validated API response to match SubstackComment interface
    const commentData: SubstackComment = {
      id: response.item.comment.id,
      body: response.item.comment.body,
      author_is_admin: false // Default value since not in response
    }

    // Validate the transformed data as well
    return decodeOrThrow(SubstackCommentCodec, commentData, 'Transformed comment data')
  }

  /**
   * Create a comment on a post
   * @param postId - The post ID
   * @param body - The comment text
   * @returns Promise<SubstackComment> - The created comment
   */
  async createComment(postId: number, body: string): Promise<SubstackComment> {
    const response = await this.publicationClient.post<unknown>(`/posts/${postId}/comments`, {
      body,
      post_id: postId
    })

    // The response structure might vary, but we can try to validate it as a comment
    return decodeOrThrow(SubstackCommentCodec, response, 'Created comment response')
  }

  /**
   * Like a comment
   * @param commentId - The comment ID
   */
  async likeComment(commentId: number): Promise<void> {
    await this.publicationClient.post(`/comment/${commentId}/reaction`, {
      reaction: '❤'
    })
  }
}
