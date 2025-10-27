import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Article } from '../services/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface CitationChartProps {
  articles: Article[]
}

const CitationChart = ({ articles }: CitationChartProps) => {

  // 统计每年爬取到的论文数量
  const yearCounts = articles.reduce((acc, article) => {
    if (article.year) {
      acc[article.year] = (acc[article.year] || 0) + 1
    }
    return acc
  }, {} as Record<number, number>)

  const sortedYears = Object.keys(yearCounts).map(Number).sort()
  
  const data = {
    labels: sortedYears.map(String),
    datasets: [
      {
        label: 'Number of Papers',
        data: sortedYears.map(year => yearCounts[year]),
        backgroundColor: 'rgba(14, 165, 233, 0.5)',
        borderColor: 'rgb(14, 165, 233)',
        borderWidth: 1,
      }
    ],
  }

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Papers by Publication Year',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Papers',
        },
        ticks: {
          stepSize: 1,
        },
      },
      x: {
        title: {
          display: true,
          text: 'Publication Year',
        },
      },
    },
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <Bar data={data} options={options} />
    </div>
  )
}

export default CitationChart