import axios from 'axios'

let BASE_URL = import.meta.env.VITE_API_URL || '/'

// If VITE_API_URL is set to an absolute http:// URL but the page
// is served over HTTPS (ngrok), coerce it to https:// to avoid
// mixed-content blocking in browsers.
if (typeof window !== 'undefined' && BASE_URL && (BASE_URL.startsWith('http://') || BASE_URL.startsWith('https://'))) {
  try {
    const parsed = new URL(BASE_URL)
    if (window.location.protocol === 'https:' && parsed.protocol === 'http:') {
      parsed.protocol = 'https:'
      BASE_URL = parsed.toString()
    }
  } catch (e) {
    // ignore malformed URL and fall back to provided value
  }
}

const client = axios.create({
  baseURL: BASE_URL,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthRequest = error.config?.url?.includes('/api/auth/login')

    if (error.response?.status === 401 && !isAuthRequest) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client