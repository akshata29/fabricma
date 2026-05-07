import axios from 'axios'

let _getToken: (() => Promise<string>) | null = null

export function setTokenProvider(fn: () => Promise<string>) {
  _getToken = fn
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

apiClient.interceptors.request.use(async (config) => {
  if (_getToken) {
    const token = await _getToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
