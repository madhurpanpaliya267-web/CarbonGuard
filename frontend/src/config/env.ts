export const config = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  POLL_INTERVAL_FAST: 5000,
  POLL_INTERVAL_NORMAL: 10000,
  POLL_INTERVAL_SLOW: 30000,
} as const
