import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { ExternalLink, Users, Calendar, Quote, Trophy, TrendingUp, Filter, Download, SortDesc, ChevronLeft, ChevronRight, FileDown, CheckSquare, Square, Settings } from 'lucide-react'
import { searchAPI, pdfAPI } from '../services/api'
import { useMutation } from 'react-query'
import CitationChart from '../components/CitationChart'

const ResultsPage = () => {
  const { searchId } = useParams<{ searchId: string }>()
  const [filterYear, setFilterYear] = useState<number | null>(null)
  const [filterMinCitations, setFilterMinCitations] = useState<number>(0)
  const [sortBy, setSortBy] = useState<string>('original')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [selectedArticles, setSelectedArticles] = useState<Set<number>>(new Set())
  const [downloadPath, setDownloadPath] = useState<string>('')
  const [showDownloadConfig, setShowDownloadConfig] = useState<boolean>(false)
  const [downloadProgress, setDownloadProgress] = useState<string>('')
  const [downloadResults, setDownloadResults] = useState<any[]>([])
  
  const itemsPerPage = 10
  
  const { data: search, isLoading } = useQuery(
    ['searchDetails', searchId],
    () => searchAPI.getSearchDetails(parseInt(searchId!)),
    { enabled: !!searchId }
  )

  // PDF下载mutation
  const downloadMutation = useMutation(pdfAPI.downloadMultiple, {
    onMutate: () => {
      setDownloadProgress('正在准备下载...')
      setDownloadResults([])
    },
    onSuccess: (data) => {
      setDownloadProgress('')
      setDownloadResults(data.results)
      const successCount = data.results.filter(r => r.success).length
      alert(`下载完成！成功下载 ${successCount}/${data.results.length} 个PDF文件`)
    },
    onError: (error: any) => {
      setDownloadProgress('')
      alert(`下载失败：${error.message}`)
    }
  })

  // 选择文章处理函数
  const handleSelectArticle = (articleIndex: number) => {
    const newSelected = new Set(selectedArticles)
    if (newSelected.has(articleIndex)) {
      newSelected.delete(articleIndex)
    } else {
      newSelected.add(articleIndex)
    }
    setSelectedArticles(newSelected)
  }

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedArticles.size === paginatedArticles.length) {
      setSelectedArticles(new Set())
    } else {
      const allIndices = paginatedArticles.map((_, index) => startIndex + index)
      setSelectedArticles(new Set(allIndices))
    }
  }

  // 下载选中的PDF
  const handleDownloadSelected = () => {
    if (selectedArticles.size === 0) {
      alert('请先选择要下载的文章')
      return
    }

    const articlesToDownload = Array.from(selectedArticles).map(index => {
      const article = sortedArticles[index]
      return {
        title: article.title,
        url: article.url || ''
      }
    }).filter(article => article.url)

    if (articlesToDownload.length === 0) {
      alert('选中的文章没有可用的URL')
      return
    }

    downloadMutation.mutate({
      articles: articlesToDownload,
      download_path: downloadPath || undefined
    })
  }

  // 下载单个PDF
  const handleDownloadSingle = async (article: any) => {
    if (!article.url) {
      alert('该文章没有可用的URL')
      return
    }

    try {
      setDownloadProgress(`正在下载: ${article.title}`)
      const result = await pdfAPI.downloadSingle(article.title, article.url, downloadPath || undefined)
      setDownloadProgress('')
      
      if (result.success) {
        alert(`PDF下载成功！保存路径：${result.filepath}`)
      } else {
        alert(`PDF下载失败：${result.message}`)
      }
    } catch (error: any) {
      setDownloadProgress('')
      alert(`下载失败：${error.message}`)
    }
  }

  if (isLoading || !search) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Apply filters first
  const filteredArticles = search.articles?.filter(article => {
    if (filterYear && article.year !== filterYear) return false
    if (article.citations < filterMinCitations) return false
    return true
  }) || []

  // Apply sorting
  const sortedArticles = [...filteredArticles].sort((a, b) => {
    switch (sortBy) {
      case 'citations':
        return (b.citations || 0) - (a.citations || 0)
      case 'citations_per_year':
        return (b.citations_per_year || 0) - (a.citations_per_year || 0)
      case 'year':
        if (!a.year && !b.year) return 0
        if (!a.year) return 1
        if (!b.year) return -1
        return b.year - a.year
      case 'title':
        return a.title.localeCompare(b.title)
      case 'original':
      default:
        return 0 // Keep original order
    }
  })

  // Apply pagination
  const totalPages = Math.ceil(sortedArticles.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedArticles = sortedArticles.slice(startIndex, endIndex)

  // Calculate statistics
  const totalArticles = search.articles?.length || 0
  const displayedArticles = sortedArticles.length
  const hasActiveFilters = filterYear !== null || filterMinCitations > 0

  const yearOptions = [...new Set(search.articles?.map(a => a.year).filter(Boolean))].sort((a, b) => b! - a!)

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Results for "{search.keyword}"
        </h1>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <p className="text-gray-600 dark:text-gray-400">
            Found {search.total_results} articles
            {totalArticles !== search.total_results && (
              <span className="ml-2 text-sm">
                ({totalArticles} successfully parsed)
              </span>
            )}
          </p>
          {hasActiveFilters && (
            <div className="mt-2 sm:mt-0">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                Filters Active: Showing {displayedArticles} of {totalArticles}
              </span>
            </div>
          )}
        </div>
      </div>

      {search.articles && search.articles.length > 0 && (
        <div className="mb-8">
          <CitationChart articles={search.articles} />
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          
          <select
            value={filterYear || ''}
            onChange={(e) => setFilterYear(e.target.value ? parseInt(e.target.value) : null)}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-sm"
          >
            <option value="">All Years</option>
            {yearOptions.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 dark:text-gray-400">
              Min Citations:
            </label>
            <input
              type="number"
              min="0"
              value={filterMinCitations}
              onChange={(e) => setFilterMinCitations(parseInt(e.target.value) || 0)}
              className="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-sm"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <SortDesc className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <label className="text-sm text-gray-600 dark:text-gray-400">
              Sort by:
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-sm"
            >
              <option value="original">Original Order</option>
              <option value="citations">Citations</option>
              <option value="citations_per_year">Citations per Year</option>
              <option value="year">Publication Year</option>
              <option value="title">Title</option>
            </select>
          </div>
          
          {hasActiveFilters && (
            <button
              onClick={() => {
                setFilterYear(null)
                setFilterMinCitations(0)
              }}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
            >
              Reset Filters
            </button>
          )}
        </div>
        
        <div className="flex flex-wrap items-center justify-between gap-4">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Showing {displayedArticles} articles (Page {currentPage} of {totalPages})
            {hasActiveFilters && (
              <span className="block text-xs text-blue-600 dark:text-blue-400">
                ({totalArticles - displayedArticles} filtered out)
              </span>
            )}
          </span>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowDownloadConfig(!showDownloadConfig)}
              className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors flex items-center space-x-1"
            >
              <Download className="h-4 w-4" />
              <span>Download PDFs</span>
            </button>
            
            {selectedArticles.size > 0 && (
              <span className="text-sm text-blue-600 dark:text-blue-400">
                {selectedArticles.size} selected
              </span>
            )}
          </div>
        </div>
      </div>

      {showDownloadConfig && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">PDF Download Configuration</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Download Path (optional)
              </label>
              <input
                type="text"
                value={downloadPath}
                onChange={(e) => setDownloadPath(e.target.value)}
                placeholder="Leave empty to use default downloads folder"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  const allIds = new Set(paginatedArticles.map((_, idx) => startIndex + idx))
                  setSelectedArticles(allIds)
                }}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                Select All on Page
              </button>
              
              <button
                onClick={() => {
                  const allIds = new Set(sortedArticles.map((_, idx) => idx))
                  setSelectedArticles(allIds)
                }}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                Select All Results
              </button>
              
              <button
                onClick={() => setSelectedArticles(new Set())}
                className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Clear Selection
              </button>
              
              <button
                onClick={handleDownloadSelected}
                disabled={selectedArticles.size === 0 || downloadMutation.isLoading}
                className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md transition-colors flex items-center space-x-1"
              >
                <FileDown className="h-4 w-4" />
                <span>
                  {downloadMutation.isLoading ? 'Downloading...' : `Download Selected (${selectedArticles.size})`}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Download Progress */}
      {downloadProgress && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-blue-800 dark:text-blue-200">{downloadProgress}</span>
          </div>
        </div>
      )}

      {/* Download Results */}
      {downloadResults.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Download Results</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {downloadResults.map((result, index) => (
              <div
                key={index}
                className={`flex items-center justify-between p-2 rounded text-sm ${
                  result.success
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                }`}
              >
                <div className="flex-1 truncate">
                  <span className="font-medium">{result.title}</span>
                  {result.filepath && (
                    <div className="text-xs opacity-75 truncate">{result.filepath}</div>
                  )}
                </div>
                <div className="ml-2">
                  {result.success ? (
                    <span className="text-green-600 dark:text-green-400">✓</span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400" title={result.error}>✗</span>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setDownloadResults([])}
            className="mt-3 px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            Clear Results
          </button>
        </div>
      )}

      <div className="space-y-4">
        {paginatedArticles.map((article, index) => {
          const globalIndex = startIndex + index
          return (
          <motion.article
            key={globalIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={selectedArticles.has(globalIndex)}
                onChange={(e) => {
                  const newSelected = new Set(selectedArticles)
                  if (e.target.checked) {
                    newSelected.add(globalIndex)
                  } else {
                    newSelected.delete(globalIndex)
                  }
                  setSelectedArticles(newSelected)
                }}
                className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              
              <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {article.url ? (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary-600 transition-colors flex items-center"
                >
                  {article.title}
                  <ExternalLink className="h-4 w-4 ml-2" />
                </a>
              ) : (
                article.title
              )}
            </h3>

            <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
              {article.authors && (
                <span className="flex items-center">
                  <Users className="h-4 w-4 mr-1" />
                  {article.authors}
                </span>
              )}
              
              {article.year && (
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {article.year}
                </span>
              )}
              
              {article.venue && (
                <span>{article.venue}</span>
              )}
              
              {article.publisher && (
                <span>{article.publisher}</span>
              )}
            </div>

            {article.description && (
              <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-3">
                <Quote className="inline h-4 w-4 mr-1" />
                {article.description}
              </p>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-sm">
                <span className="flex items-center text-primary-600 dark:text-primary-400 font-medium">
                  <Trophy className="h-4 w-4 mr-1" />
                  {article.citations} citations
                </span>
                
                {article.citations_per_year > 0 && (
                  <span className="flex items-center text-green-600 dark:text-green-400 font-medium">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    {article.citations_per_year.toFixed(1)}/year
                  </span>
                )}
              </div>
              
              {article.url && (
                <button
                  onClick={() => handleDownloadSingle(article)}
                  disabled={downloadProgress.includes(article.title)}
                  className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded transition-colors flex items-center space-x-1"
                  title="Download PDF"
                >
                  <FileDown className="h-3 w-3" />
                  <span>PDF</span>
                </button>
              )}
            </div>
              </div>
            </div>
          </motion.article>
        )})}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 mt-8">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </button>
          
          <div className="flex items-center space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum
              if (totalPages <= 5) {
                pageNum = i + 1
              } else if (currentPage <= 3) {
                pageNum = i + 1
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i
              } else {
                pageNum = currentPage - 2 + i
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-2 text-sm rounded-md ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
          </div>
          
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}

export default ResultsPage