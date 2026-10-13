import axios from 'axios'

// Axios-Instanz erstellen
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:5002' : ''),  // Produktion: gleicher Ursprung wie das Frontend
  timeout: 300000, // 5 Minuten Timeout (die Generierung des Körpers kann länger dauern)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request-Interceptor
service.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response-Interceptor (Fehlertoleranz-Retry-Mechanismus)
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // Wenn der Rückgabestatuscode nicht success ist, Fehler auslösen
    if (!res.success && res.success !== undefined) {
      console.error('API Error:', res.error || res.message || 'Unknown error')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }
    
    return res
  },
  error => {
    console.error('Response error:', error)
    
    // Timeout behandeln
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }
    
    // Netzwerkfehler behandeln
    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection')
    }
    
    return Promise.reject(error)
  }
)

// Request-Funktion mit Retry
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
