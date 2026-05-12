# Recipe Extractor AI (Phase 2)

A premium web application that extracts structured recipes from YouTube cooking videos using **yt-dlp** and **Google Gemini 3 Flash**.

## Features
- 🚀 **AI-Powered**: Uses Gemini 3 Flash to parse transcripts and descriptions.
- 🎨 **Premium UI**: Modern dark mode with glassmorphism and smooth animations.
- 📊 **Structured Data**: Get ingredients, instructions, prep time, and more in a clean format.
- 📋 **One-Click Copy**: Easily copy the recipe to your clipboard.

## Tech Stack
- **Backend**: Python (FastAPI)
- **Frontend**: React + Vite + Framer Motion
- **AI**: Google Generative AI (Gemini 1.5 Flash)
- **Tools**: yt-dlp for video metadata extraction.

## Setup

### 1. Backend
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env`:
   Add your `GOOGLE_API_KEY` to the `.env` file.
3. Start the API:
   ```bash
   python main.py
   ```

### 2. Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

## Next Steps (Phase 3)
- [ ] Save recipes to a database (Supabase/Firebase).
- [ ] Multi-language support for transcripts.
- [ ] Image extraction from video thumbnails.
