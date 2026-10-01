export interface ApiResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PaginatedRequest {
  page?: number
  page_size?: number
}

export interface ApiError {
  detail: string
}
