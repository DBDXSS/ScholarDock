# ScholarDock

A modern, full-stack web application for searching and analyzing academic articles from Google Scholar. Built with FastAPI backend and React TypeScript frontend.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18.2+-blue.svg)

## ✨ Features

### 🔍 Advanced Search
- Search Google Scholar with customizable parameters
- Filter by publication year range
- Sort results by relevance or publication date
- Support for up to 1000 results per search

### 📊 Data Visualization
- Interactive charts showing citation trends over time
- Publication distribution analysis
- Real-time data filtering and exploration

### 📥 PDF Download
- Batch PDF download functionality
- Individual PDF download for articles
- Configurable download path and concurrency
- Download progress tracking and results reporting

### � Data Management
- Search history with SQLite database storage
- Export results in multiple formats (CSV, JSON, Excel, BibTeX)
- Delete and manage previous searches
- Complete article abstracts without truncation

### 🎨 Modern UI/UX
- Responsive design with Tailwind CSS
- Dark mode support
- Smooth animations with Framer Motion
- Real-time search progress indicators

### 🚀 Performance
- Asynchronous backend with FastAPI
- Efficient data fetching with React Query
- Automatic retry mechanism for failed requests
- Selenium fallback for CAPTCHA handling

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Chrome/Chromium browser (for Selenium fallback)

## 🛠️ Installation

> **Windows用户请参考**: [Windows安装指南](README-Windows.md) 获取详细的Windows安装说明。

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd scholardock
```

### 2. Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the backend directory (optional):
```env
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./data/scholar.db
USE_SELENIUM_FALLBACK=true
```

### 3. Setup Frontend

```bash
cd ../frontend
npm install
```

## 🚀 Running the Application

### Quick Start (Recommended)

```bash
# Start both frontend and backend
./run.sh

# Stop all services
./stop.sh
```

### Manual Start

```bash
# Terminal 1 - Backend
cd backend
python run.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### Service URLs

The services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001`
- API Documentation: `http://localhost:8001/docs`

## 📖 API Documentation

Once the backend is running, visit `http://localhost:8001/docs` for interactive API documentation.

### Main Endpoints

- `POST /api/search` - Perform a new search
- `GET /api/searches` - Get search history
- `GET /api/search/{search_id}` - Get search details
- `GET /api/export/{search_id}` - Export search results
- `POST /api/download/multiple` - Download multiple PDFs
- `DELETE /api/search/{search_id}` - Delete a search

## 🏗️ Project Structure

```
scholardock/
├── backend/
│   ├── api/
│   │   └── main.py          # FastAPI application
│   ├── core/
│   │   ├── config.py        # Configuration settings
│   │   └── database.py      # Database setup
│   ├── models/
│   │   └── article.py       # Data models
│   ├── services/
│   │   ├── original_spider.py # Web scraping logic
│   │   ├── export.py        # Export functionality
│   │   └── pdf_downloader.py # PDF download service
│   └── run.py               # Backend entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── contexts/        # React contexts
│   └── package.json
├── data/                    # SQLite database storage
├── downloads/               # PDF download directory
└── README.md
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/core/config.py` or create a `.env` file:

- `DATABASE_URL`: SQLite database connection string
- `REQUEST_DELAY`: Delay between requests (default: 0.5s)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `USE_SELENIUM_FALLBACK`: Enable Selenium for CAPTCHA (default: true)

### Frontend Configuration

Edit `frontend/vite.config.ts` for proxy settings and development server configuration.

## 🎯 Usage

1. **Search Articles**: Enter keywords and optional filters on the search page
2. **View Results**: Browse articles with citation counts and publication details
3. **Download PDFs**: Select articles and download PDFs individually or in batch
4. **Visualize Data**: Analyze citation trends with interactive charts
5. **Export Data**: Download results in your preferred format (CSV, JSON, Excel, BibTeX)
6. **Manage History**: Access and manage previous searches

## 🐛 Troubleshooting

### Common Issues

1. **CAPTCHA Detection**
   - The application will automatically open a browser for manual CAPTCHA solving
   - Ensure Chrome/Chromium is installed

2. **Rate Limiting**
   - Increase `REQUEST_DELAY` in configuration
   - Reduce the number of results per search

3. **Database Errors**
   - Ensure the `data` directory exists and has write permissions
   - Check database connection string in configuration

4. **PDF Download Issues**
   - Ensure the `downloads` directory exists and has write permissions
   - Check network connectivity for PDF access
   - Some PDFs may not be publicly accessible

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React and TypeScript communities
- All contributors to this project
- Thanks for [JessyTsui's opensource work!](https://github.com/JessyTsui/ScholarDock)