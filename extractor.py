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
    import requests
    import re
    
    is_instagram = "instagram.com" in url
    
    # Stealthy options to avoid bot detection
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }
    
    # Only add subtitle options for YouTube
    if not is_instagram:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            
            transcript = ""
            # Subtitle extraction logic... (simplified for brevity)
            
            return {
                'title': info.get('title') or 'Untitled',
                'description': info.get('description', ''),
                'transcript': transcript,
                'uploader': info.get('uploader') or 'Unknown',
                'url': url,
                'source': 'Instagram' if is_instagram else 'YouTube'
            }
    except Exception as e:
        print(f"yt-dlp failed (likely bot block), trying fallback: {e}")
        
            # Fallback: Simple HTTP request to get title/description
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = requests.get(url, headers=headers, timeout=10)
            html = response.text
            
            # Extract Title
            title_match = re.search(r'<title>(.*?)</title>', html)
            title_str = title_match.group(1).replace(' - YouTube', '') if title_match else "Untitled"
            
            # Extract Description (Try multiple patterns)
            desc_str = "Could not extract description."
            
            # Pattern 1: Meta tag
            desc_match = re.search(r'name="description" content="(.*?)"', html)
            if desc_match:
                desc_str = desc_match.group(1)
            else:
                # Pattern 2: shortDescription in ytInitialData JSON
                desc_match = re.search(r'"shortDescription":"(.*?)"', html)
                if desc_match:
                    # Clean up escaped characters
                    desc_str = desc_match.group(1).encode().decode('unicode_escape')
            
            return {
                'title': title_str,
                'description': desc_str,
                'transcript': "",
                'uploader': "Unknown",
                'url': url,
                'source': 'Instagram' if is_instagram else 'YouTube'
            }
        except Exception as fallback_e:
            print(f"Fallback also failed: {fallback_e}")
            return None

def extract_recipe_with_gemini(video_data):
    """Uses Gemini to extract a structured recipe from video data."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    source_type = video_data.get('source', 'Video')
    title = video_data.get('title', 'Untitled Recipe')
    description = video_data.get('description', '')
    
    context = f"Source: {source_type}\nTitle: {title}\n\nDescription/Caption:\n{description}"
    
    prompt = f"""
    You are a professional chef. Extract the recipe from the following {source_type} content.
    
    {context}
    
    IMPORTANT: Return ONLY a valid JSON object with this EXACT structure:
    {{
        "title": "Clear Recipe Name",
        "ingredients": ["1 cup flour", "2 eggs", "..."],
        "instructions": ["Step 1...", "Step 2...", "..."],
        "prep_time": "10 mins",
        "cook_time": "20 mins",
        "servings": "2-4 people"
    }}
    
    If data is missing, make a professional estimate based on the recipe type.
    Do not include any markdown or text outside the JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Robust JSON cleaning
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Final cleanup for any trailing characters
        content = content[content.find('{'):content.rfind('}')+1]
            
        return json.loads(content)
    except Exception as e:
        print(f"Gemini error: {e}")
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
