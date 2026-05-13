from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import extractor
import os

app = FastAPI(title="Recipe Extractor API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "Recipe Extractor API is running!"}

@app.post("/extract")
async def extract_recipe(request: ExtractRequest):
    print(f"Received extraction request for: {request.url}")
    
    # 1. Fetch video data
    video_data = extractor.get_video_data(request.url)
    if not video_data:
        print(f"ERROR: Fetching video data failed for {request.url}")
        raise HTTPException(status_code=400, detail="Could not fetch video data. YouTube might be blocking the request. Please try again in a moment.")
    
    # 2. Extract recipe using Gemini
    print(f"DEBUG: Successfully fetched video data. Proceeding to Gemini...")
    recipe = extractor.extract_recipe_with_gemini(video_data)
    if not recipe or not recipe.get('title'):
        print(f"ERROR: Gemini extraction failed or returned no recipe for {request.url}")
        raise HTTPException(status_code=404, detail="Could not find a recipe in this video. Please ensure the recipe is mentioned in the video or description.")
    
    return recipe

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
