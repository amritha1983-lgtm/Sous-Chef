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
        raise HTTPException(status_code=400, detail="Could not fetch video data from the provided URL.")
    
    # 2. Extract recipe using Gemini
    recipe = extractor.extract_recipe_with_gemini(video_data)
    if not recipe or not recipe.get('title'):
        raise HTTPException(status_code=404, detail="Could not find a recipe in this video. Please try a different URL or ensure the recipe is in the description.")
    
    return recipe

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
