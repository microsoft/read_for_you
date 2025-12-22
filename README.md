# 📚 Read for You

An intelligent PDF reading and recognition system that supports OCR recognition, Text-to-Speech (TTS), and AI conversation features for PDF documents.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)
![Django](https://img.shields.io/badge/Django-4.2+-orange.svg)

## 🌟 Project Overview

Read for You is a full-stack web application designed to provide users with an intelligent PDF reading experience. The system integrates Azure Document Intelligence for OCR recognition, supports multilingual text extraction, and provides text-to-speech functionality to help users read documents more conveniently.

### Core Features

- 📄 **PDF Upload & Management**: Support for PDF file upload, preview, and categorized management
- 🔍 **Intelligent OCR Recognition**: Document recognition powered by Azure Document Intelligence
- 🗣️ **Text-to-Speech (TTS)**: Convert recognized text to speech with multilingual support
- 🤖 **AI Chat Assistant**: Integrated AI chat functionality to assist with document understanding
- 🌐 **Multilingual Support**: Support for Chinese, English, and other languages
- 💾 **Cloud Storage Integration**: File storage using Azure Blob Storage
- 📱 **Responsive Design**: Optimized for desktop and mobile devices

## 🏗️ Technology Stack

### Backend Technologies

- **Framework**: Django 4.2.16
- **Core Dependencies**:
  - `django-cors-headers`: Cross-origin request handling
  - `PyPDF2`: PDF file processing
  - `azure-storage-blob`: Azure Blob Storage integration
  - `requests`: HTTP request handling
  - `python-dotenv`: Environment variable management

### Frontend Technologies

- **Framework**: Vue 3.5+
- **Build Tool**: Vite 7.1+
- **Core Dependencies**:
  - `pdfjs-dist`: PDF rendering
  - `pdf-lib`: PDF manipulation
  - `@echogarden/fvad-wasm`: Voice activity detection
  - `@azure/static-web-apps-cli`: Azure Static Web Apps deployment

### Cloud Services

- **Azure Document Intelligence**: OCR document recognition
- **Azure Blob Storage**: File storage
- **Azure App Service**: Backend deployment
- **Azure Static Web Apps**: Frontend deployment

## 📁 Project Structure

```
ReadForYou_Web/
├── backend/                    # Django backend
│   ├── manage.py              # Django management script
│   ├── requirements.txt       # Python dependencies
│   ├── db.sqlite3            # SQLite database
│   ├── read_for_you/         # Main application
│   │   ├── settings.py       # Django settings
│   │   ├── urls.py           # URL routing
│   │   ├── views.py          # View functions
│   │   ├── constants.py      # Constants configuration
│   │   ├── Services/         # Service layer
│   │   │   ├── AzureBlobService.py    # Azure Blob service
│   │   │   ├── PDFService.py          # PDF processing service
│   │   │   ├── ProcessingService.py   # Processing service
│   │   │   └── RecognitionServices.py # Recognition service
│   │   └── static/           # Static files
│   └── scripts/              # Utility scripts
│       └── traverse_books.py # Book traversal script
│
└── frontend/                  # Vue frontend
    ├── package.json          # Node.js dependencies
    ├── vite.config.js        # Vite configuration
    ├── index.html            # Entry HTML
    ├── src/
    │   ├── App.vue           # Main app component
    │   ├── main.js           # Application entry
    │   ├── constants.js      # Constants configuration
    │   ├── components/       # Vue components
    │   │   ├── IndexPage.vue      # Home page
    │   │   ├── ReadingPage.vue    # Reading page
    │   │   ├── TopNav.vue         # Top navigation
    │   │   └── AIChat/            # AI chat components
    │   └── utils/            # Utility functions
    │       ├── i18n.js            # Internationalization
    │       ├── PDFService.js      # PDF service
    │       ├── TTS.js             # TTS service
    │       ├── TTSManager.js      # TTS manager
    │       ├── TTSPlayer.js       # TTS player
    │       └── IndexedDBService.js # Local storage
    └── public/               # Public resources
```

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/junyingshao_microsoft/ReadForYou.git
cd ReadForYou_Web/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file and configure the following environment variables:
```env
# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=your_container_name

# Azure Document Intelligence
DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
DOCUMENT_INTELLIGENCE_KEY=your_key
```

5. **Database migration**
```bash
python manage.py migrate
```

6. **Run development server**
```bash
python manage.py runserver
```

The backend service will start at `http://127.0.0.1:8000`.

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure API endpoint**

Edit the `src/constants.js` file to configure the backend API address:
```javascript
export const API_BASE_URL = 'http://127.0.0.1:8000';
```

4. **Run development server**
```bash
npm run dev
```

The frontend service will start at `http://localhost:5173`.

5. **Build for production**
```bash
npm run build
```

## 🔧 API Documentation

### 1. PDF Recognition API

**Endpoint**: `POST /recognition`

**Description**: Upload PDF file and perform OCR recognition

**Parameters**:
- `file`: PDF file (multipart/form-data)
- `pageNum`: Page range (e.g., "1-3" or "1,3,5")
- `language`: Language code (URL parameter, e.g., "zh-CN")

**Response Example**:
```json
{
  "status": "success",
  "data": {
    "text": "Recognized text content",
    "pdf": "data:application/pdf;base64,..."
  }
}
```

### 2. Get Cover Images

**Endpoint**: `GET /getCoverImages`

**Description**: Get all book cover image URLs

**Response Example**:
```json
{
  "success": true,
  "count": 10,
  "images": [
    {
      "url": "https://...",
      "name": "book_cover_1.jpg"
    }
  ]
}
```

### 3. Get Stored Data

**Endpoint**: `GET /getStoragedData`

**Description**: Retrieve files from Azure Blob Storage

**Parameters**:
- `prefix`: File path prefix
- `type`: File type (pdf, jpg, png, etc.)

### 4. Get Book Metadata

**Endpoint**: `GET /getBookMetadata`

**Description**: Get metadata information for a specific book

**Parameters**:
- `prefix`: Book path prefix

## 🌐 Deployment

### Production Deployment

**Backend Deployment (Azure App Service)**:
- Deployment URL: https://readforyou-fwanhpcfatfedqce.canadacentral-01.azurewebsites.net
- Using Gunicorn as WSGI server

**Frontend Deployment (Azure Static Web Apps)**:
- Build static files using `npm run build`
- Deploy via Azure Static Web Apps CLI

**Server Information**:
- VM IP: 4.193.237.95
- Domain: https://readforyou.xyz

## 📝 Main Modules

### PDF Service (PDFService)

- `extractPDF`: Extract PDF pages based on page range
- `normalizePageRange`: Normalize page range format

### Azure Blob Service (AzureBlobService)

- `uploadFile`: Upload files to Azure Blob Storage
- `downloadFile`: Download files from Azure Blob Storage
- `getAllCoverImages`: Get all cover images

### Recognition Service (RecognitionServices)

- Integrated with Azure Document Intelligence API
- Support for synchronous and asynchronous recognition
- Multilingual document recognition

### Processing Service (ProcessingService)

- Coordinate PDF processing and recognition workflow
- Handle formatting and storage of recognition results

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details

## 📞 Contact

- Project Maintainer: junyingshao_microsoft
- Repository: [ReadForYou](https://github.com/junyingshao_microsoft/ReadForYou)

## 📚 Documentation

For more detailed project design documentation, please visit:
[Read for You Project Design](https://microsoftapc-my.sharepoint.com/:w:/g/personal/t-junhaoleng_microsoft_com/EcmfYScZywVOvrIsNFq2VGoBSRl81uomQ8AQ3XK5se5lzg?e=SqfkNw)

## 🙏 Acknowledgments

- Azure Document Intelligence
- Azure Blob Storage
- Vue.js Community
- Django Community

---

⭐ If this project helps you, please give us a Star!

