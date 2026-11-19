# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Read for You** is a web application that extracts text and multimedia content from PDF documents using Azure Document Intelligence (Intelligent OCR), displays them in an accessible format, and provides text-to-speech (TTS) capabilities for reading aloud.

### Technology Stack

- **Frontend**: Vue 3 + Vite (Composition API with `<script setup>`)
- **Backend**: Django 5.2
- **PDF Processing**: pdf-lib, pdfjs-dist, pypdf
- **External Services**:
  - Azure Document Intelligence for OCR/document analysis
  - Custom TTS service (WebSocket-based)
  - Multimodal AI chat service (WebSocket-based)

## Project Structure

```
ReadForYou/
├── frontend/read_for_you/          # Vue 3 frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── IndexPage.vue       # PDF upload and page selection
│   │   │   └── ReadingPage.vue     # Main reading interface with TTS
│   │   ├── utils/
│   │   │   ├── extractPDF.js       # PDF page extraction utilities
│   │   │   └── TTS.js              # Text-to-speech API integration
│   │   ├── constants.js            # API endpoints configuration
│   │   └── App.vue                 # Root component with routing
│   └── docs/
│       └── TTS_Strategy.md         # Comprehensive TTS implementation documentation
└── backend/                        # Django backend
    └── read_for_you/
        ├── views.py                # API endpoints
        ├── Services/
        │   ├── PDFService.py       # PDF extraction logic
        │   └── RecognitionServices.py  # Document Intelligence integration
        └── settings.py             # Django configuration
```

## Development Commands

### Frontend (Vue 3 + Vite)

```bash
cd frontend/read_for_you

# Install dependencies
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend (Django)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server (http://localhost:8000)
python manage.py runserver

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## API Endpoints Configuration

Configure these in `frontend/read_for_you/src/constants.js`:

- **backendUrl**: Django backend (`http://localhost:8000`)
- **TTSUrl**: Text-to-speech service endpoint
- **aiChatUrl**: WebSocket URL for multimodal AI chat

Backend service URLs in `backend/read_for_you/settings.py`:

- **SyncAnalysisUrl**: Azure Document Intelligence sync endpoint
- **AsyncAnalysisUrl**: Azure Document Intelligence async endpoint
- **GetAsyncResultUrl**: Check async analysis results

## Key Architecture Patterns

### TTS (Text-to-Speech) System

**Critical**: The TTS implementation uses a sophisticated strategy documented in `frontend/read_for_you/docs/TTS_Strategy.md`. Key features:

1. **Auto-preload on page load**: TTS audio is preloaded immediately when `AnalysisResult` is available (no delay)
2. **Smart caching**: Audio is cached and reused when re-playing the same page
3. **Page-switch preload**: If user has used TTS before, new pages are preloaded automatically
4. **Staggered concurrent requests**: Elements are fetched with 50ms delays to preserve order
5. **Buffering strategy**: Playback starts when 20% + first 3 elements are loaded

**State management** (`ReadingPage.vue`):
- `audioMap`: Map storing elementIndex → audioBlob
- `isLoadingAudio`: Loading state for UI feedback
- `hasUsedTTS`: Tracks if user has used TTS (for smart preload)
- Cache is cleared only on page switch, preserved on stop/replay

### Document Display with AI Descriptions

The ReadingPage component displays multiple content types with AI-generated descriptions:

- **Paragraphs**: Plain text content
- **Figures**: Images with `detailDescription` from Document Intelligence
- **Tables**: Tables with AI-generated summary descriptions
- **Formulas**: LaTeX formulas with source code display

**Adaptive layout** (based on image aspect ratio):
- Wide images (ratio > 1.4): Vertical layout (image top, description bottom)
- Square/tall images (ratio ≤ 1.4): Horizontal layout (image left 1fr, description right 350px)

### Data Flow

```
1. IndexPage: User uploads PDF and selects pages
   ↓
2. extractPDF.js: Extract selected pages, convert to images
   ↓
3. Backend /api/recognition: Send to Azure Document Intelligence
   ↓
4. Backend returns structured data (paragraphs, tables, figures, formulas)
   ↓
5. ReadingPage: Display content with localStorage caching
   ↓
6. Auto-preload TTS: Fetch speech audio for all elements
   ↓
7. User clicks "Read Aloud": Instant playback using preloaded audio
```

### LocalStorage Usage

The app heavily uses localStorage for state persistence:

- `analysisResult`: Document Intelligence response (all pages)
- `extractedPDFPages`: Array of PDF page image URLs
- `hasUsedTTS`: Boolean flag for smart preload behavior

## Important Implementation Details

### ReadingPage.vue Component

**Reading blocks**: Elements are grouped by `continueFromPrevious` property to determine paragraph boundaries.

**Container selection**: Figure/table/formula containers are fully focusable and selectable (not just the image). Use `tabindex="0"` and `role="group"` on containers.

**Focus management**: Implements context preservation when navigating to AI chat and back, storing scroll position and focused element.

### PDF Processing

**Backend** (`PDFService.py`):
- Uses pypdf to extract specific page ranges
- Returns in-memory PDF bytes for upload to Azure

**Frontend** (`extractPDF.js`):
- Uses pdf-lib to extract pages
- Converts to images for preview using pdfjs-dist
- Base64 encodes images for localStorage

### TTS Audio Caching Strategy

When implementing TTS features:

1. **Never clear cache on stop**: `stopReading()` must NOT clear `audioMap`
2. **Clear only on page switch**: `watch(currentPage)` clears old page cache
3. **Check cache before loading**: `startReading()` checks if `audioMap.size > 0`
4. **Preload trigger**: Call `preloadCurrentPageTTS()` when `AnalysisResult` is loaded

## Styling Conventions

- **AI-generated content**: Blue gradient background (#f0f9ff → #e0f2fe) with left border
- **AI badges**: Use 🤖 emoji with gradient background (#0ea5e9 → #0284c7)
- **Focus states**: Blue outline (#409eff) with light background
- **Currently reading**: Purple gradient with left border animation

## Common Pitfalls

1. **Don't add delays to TTS preload**: Check `AnalysisResult.value` and call preload immediately
2. **Don't clear audio cache on stop**: Users expect instant replay
3. **Container vs child focus**: Set `tabindex` on container, not on nested elements
4. **Image aspect ratio**: Use `getImageLayoutClass()` to determine layout (threshold: 1.4)
5. **LocalStorage limits**: Large PDFs with many pages may hit storage limits

## Testing Workflow

1. Upload a multi-page PDF with various content types (text, images, tables, formulas)
2. Verify page extraction and preview display
3. Check Document Intelligence response structure
4. Test TTS preload (check console for "🚀 Preloading TTS" messages)
5. Click "Read Aloud" - should play instantly if preloaded
6. Stop and replay - should reuse cached audio
7. Switch pages - verify old cache cleared, new page preloaded
8. Test keyboard navigation (Tab, focus states)
9. Test responsive layout (resize window < 1024px)

## Version History

- **v4.0**: Smart TTS preload, audio caching, adaptive layouts for AI descriptions
- **v3.0**: Staggered concurrent TTS with buffering strategy
