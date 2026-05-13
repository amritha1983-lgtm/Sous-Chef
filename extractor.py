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
    image: Optional[str] = Field(description="Thumbnail URL of the video")

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
        'noplaylist': True,
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
            try:
                if 'requested_subtitles' in info and 'en' in info['requested_subtitles']:
                    sub_url = info['requested_subtitles']['en']['url']
                    print(f"DEBUG: Found subtitles at {sub_url[:50]}...")
                    sub_response = requests.get(sub_url, timeout=5)
                    transcript = sub_response.text
                elif 'subtitles' in info and 'en' in info['subtitles']:
                    # Fallback to general subtitles list
                    sub_url = info['subtitles']['en'][0]['url']
                    sub_response = requests.get(sub_url, timeout=5)
                    transcript = sub_response.text
            except Exception as sub_e:
                print(f"DEBUG: Subtitle extraction failed: {sub_e}")
            
            return {
                'title': info.get('title') or 'Untitled',
                'description': info.get('description', ''),
                'transcript': transcript,
                'uploader': info.get('uploader') or 'Unknown',
                'url': url,
                'thumbnail': info.get('thumbnail'),
                'source': 'Instagram' if is_instagram else 'YouTube'
            }
    except Exception as e:
        print(f"yt-dlp failed (likely bot block), trying fallback: {e}")
        
            # Fallback: Simple HTTP request to get title/description
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
            }
            response = requests.get(url, headers=headers, timeout=10)
            html = response.text
            
            # Extract Title - more robust pattern
            title_match = re.search(r'<title>(.*?)</title>', html)
            title_str = title_match.group(1).replace(' - YouTube', '') if title_match else "Untitled"
            
            # If title is just "YouTube", it's likely a bot check or home page
            if title_str.strip() == "YouTube":
                title_str = "Unknown Recipe"
            
            # Extract Description (Try multiple patterns)
            desc_str = ""
            
            # Look for the full description in the JSON blob
            # Pattern: "shortDescription":"..."
            json_desc_match = re.search(r'"shortDescription":"(.*?)(?<!\\)"', html)
            if json_desc_match:
                try:
                    desc_str = json_desc_match.group(1).encode().decode('unicode_escape')
                except:
                    desc_str = json_desc_match.group(1)
            
            if not desc_str or len(desc_str) < 20:
                # Try the meta tag
                desc_match = re.search(r'name="description" content="(.*?)"', html)
                if desc_match:
                    desc_str = desc_match.group(1)
            
            # Extract Thumbnail
            thumb_match = re.search(r'property="og:image" content="(.*?)"', html)
            thumb_url = thumb_match.group(1) if thumb_match else None
            
            # If we still have nothing, we can't do much
            if not desc_str:
                print("DEBUG: Fallback failed to find any description text.")
            
            return {
                'title': title_str,
                'description': desc_str,
                'transcript': "",
                'uploader': "Unknown",
                'url': url,
                'thumbnail': thumb_url,
                'source': 'Instagram' if is_instagram else 'YouTube'
            }
        except Exception as fallback_e:
            print(f"Fallback also failed: {fallback_e}")
            return None

def extract_recipe_with_gemini(video_data):
    """Uses Gemini to extract a structured recipe from video data."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    source_type = video_data.get('source', 'Video')
    title = video_data.get('title', 'Untitled Recipe')
    description = video_data.get('description', '')
    transcript = video_data.get('transcript', '')
    
    context = f"Source: {source_type}\nTitle: {title}\n\nDescription/Caption:\n{description}\n\nTranscript Content:\n{transcript}"
    
    prompt = f"""
    You are a professional chef. Extract the EXACT recipe details from the provided {source_type} content.
    
    {context}
    
    IMPORTANT: Return ONLY a valid JSON object. 
    If the content does not contain actual recipe details (ingredients or steps), return an empty JSON object {{}}.
    
    DO NOT HALLUCINATE. If a specific detail (like prep time or an ingredient quantity) is not explicitly mentioned, set it to null or "Not mentioned". Do not make estimates.
    
    JSON Structure:
    {{
        "title": "Clear Recipe Name",
        "ingredients": ["1 cup flour", "2 eggs", "..."],
        "instructions": ["Step 1...", "Step 2...", "..."],
        "prep_time": "10 mins or null",
        "cook_time": "20 mins or null",
        "servings": "2-4 people or null"
    }}
    
    Do not include any markdown or text outside the JSON.
    """
    
    try:
        print(f"DEBUG: Sending to Gemini - Title: {title}")
        print(f"DEBUG: Description length: {len(description)}")
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Robust JSON cleaning
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Final cleanup for any trailing characters
        content = content[content.find('{'):content.rfind('}')+1]
            
        recipe_json = json.loads(content)
        # Add thumbnail from video data if not present in Gemini output
        if 'image' not in recipe_json or not recipe_json['image']:
            recipe_json['image'] = video_data.get('thumbnail')
            
        return recipe_json
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
