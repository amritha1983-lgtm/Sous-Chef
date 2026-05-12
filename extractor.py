import os
import json
import yt_dlp
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import sys

# Load environment variables
load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment or .env file.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

class Recipe(BaseModel):
    title: str = Field(description="The title of the recipe")
    ingredients: List[str] = Field(description="List of ingredients with quantities")
    instructions: List[str] = Field(description="Step-by-step instructions")
    prep_time: Optional[str] = Field(description="Preparation time")
    cook_time: Optional[str] = Field(description="Cooking time")
    servings: Optional[str] = Field(description="Number of servings")

def get_video_data(url):
    """Extracts metadata and transcript from YouTube or Instagram video."""
    is_instagram = "instagram.com" in url
    
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': 'temp_subs_%(id)s',
    }
    
    # Only add subtitle options for YouTube
    if not is_instagram:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
        })
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=not is_instagram) # Download only if needed for subs
            video_id = info.get('id')
            
            transcript = ""
            if not is_instagram:
                import glob
                sub_files = glob.glob(f"temp_subs_{video_id}.en.*")
                if sub_files:
                    sub_file = sub_files[0]
                    with open(sub_file, 'r', encoding='utf-8') as f:
                        transcript = f.read()
                    for f_path in sub_files:
                        try: os.remove(f_path)
                        except: pass
            
            return {
                'title': info.get('title') or info.get('description', 'Untitled')[:50],
                'description': info.get('description', ''),
                'transcript': transcript,
                'uploader': info.get('uploader') or info.get('webpage_url_basename'),
                'url': url,
                'source': 'Instagram' if is_instagram else 'YouTube'
            }
        except Exception as e:
            print(f"Error fetching video data: {e}")
            return None

def extract_recipe_with_gemini(video_data):
    """Uses Gemini to extract a structured recipe from video data."""
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    # Combine description and transcript for better context
    source_type = video_data.get('source', 'Video')
    context = f"Source: {source_type}\nTitle: {video_data['title']}\n\nDescription/Caption:\n{video_data['description']}"
    
    if video_data.get('transcript'):
        # Clean up VTT/SRT tags if present for better Gemini readability
        import re
        clean_transcript = re.sub(r'\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}.*\n', '', video_data['transcript'])
        clean_transcript = re.sub(r'<[^>]*>', '', clean_transcript)
        context += f"\n\nTranscript:\n{clean_transcript[:10000]}" # Limit context size
    else:
        context += f"\n\n(No transcript available, please extract strictly from the title and caption/description provided above. For {source_type} reels, the recipe is usually in the caption.)"
    
    prompt = f"""
    You are a professional chef and data extractor. 
    Below is the information from a {source_type} cooking post. 
    Please extract the recipe and return it as a VALID JSON object.
    
    {context}
    
    The JSON structure MUST follow this schema:
    {{
        "title": "Recipe Title",
        "ingredients": ["quantity + unit + item", ...],
        "instructions": ["step 1", "step 2", ...],
        "prep_time": "e.g., 15 mins",
        "cook_time": "e.g., 30 mins",
        "servings": "e.g., 4 people"
    }}
    
    If any field is missing, use "N/A" or estimate based on context.
    Return ONLY the JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up markdown if Gemini wraps it
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            # Fallback for generic code blocks
            lines = content.split('\n')
            if lines[0].startswith('```'):
                content = '\n'.join(lines[1:-1]).strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error extracting recipe with Gemini: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <youtube_url>")
        return

    url = sys.argv[1]
    print(f"--- Extracting data for: {url} ---")
    
    video_data = get_video_data(url)
    if not video_data:
        return

    print("--- Processing with Gemini ---")
    recipe = extract_recipe_with_gemini(video_data)
    
    if recipe:
        print("\n--- Extracted Recipe (JSON) ---")
        print(json.dumps(recipe, indent=2))
        
        # Save to file
        output_file = "latest_recipe.json"
        with open(output_file, "w") as f:
            json.dump(recipe, f, indent=2)
        print(f"\nRecipe saved to {output_file}")
    else:
        print("Failed to extract recipe.")

if __name__ == "__main__":
    main()
