import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface SearchRequest {
  keyword: string
  num_results: number
  start_year?: number
  end_year?: number
}

export interface Article {
  id?: number
  title: string
  authors?: string
  venue?: string
  publisher?: string
  year?: number
  citations: number
  citations_per_year: number
  description?: string
  url?: string
  created_at?: string
}

export interface SearchResponse {
  search_id: number
  keyword: string
  total_results: number
  articles: Article[]
  message: string
}

export interface Search {
  id: number
  keyword: string
  start_year?: number
  end_year?: number
  total_results: number
  created_at: string
  articles?: Article[]
}


export const searchAPI = {
  search: async (params: SearchRequest): Promise<SearchResponse> => {
    const { data } = await api.post<SearchResponse>('/search', params)
    return data
  },

  getSearchHistory: async (skip = 0, limit = 20): Promise<Search[]> => {
    const { data } = await api.get<Search[]>('/searches', { params: { skip, limit } })
    return data
  },

  getSearchDetails: async (searchId: number): Promise<Search> => {
    const { data } = await api.get<Search>(`/search/${searchId}`)
    return data
  },

  deleteSearch: async (searchId: number): Promise<void> => {
    await api.delete(`/search/${searchId}`)
  },

  exportResults: async (searchId: number, format: string): Promise<Blob> => {
    const { data } = await api.get(`/export/${searchId}`, {
      params: { format },
      responseType: 'blob',
    })
    return data
  },
}

// PDF下载相关接口
export interface PDFDownloadRequest {
  articles: Array<{
    title: string
    url: string
  }>
  download_path?: string
}

export interface PDFDownloadResult {
  title: string
  url: string
  filepath: string | null
  success: boolean
  error?: string
}

export interface PDFDownloadResponse {
  success: boolean
  message: string
  results: PDFDownloadResult[]
}

export const pdfAPI = {
  downloadMultiple: async (request: PDFDownloadRequest): Promise<PDFDownloadResponse> => {
    const { data } = await api.post<PDFDownloadResponse>('/download-pdf', request)
    return data
  },

  downloadSingle: async (
    title: string,
    url: string,
    downloadPath?: string
  ): Promise<{
    success: boolean
    message: string
    filepath: string | null
  }> => {
    const { data } = await api.post('/download-single-pdf', null, {
      params: { title, url, download_path: downloadPath }
    })
    return data
  },
}

export default api