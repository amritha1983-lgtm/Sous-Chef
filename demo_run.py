import json

# This is a demonstration of what the Phase 1 backend produces.
# It simulates the extraction process from a YouTube video transcript.

SAMPLE_TRANSCRIPT = """
Hey everyone! Today I'm going to show you how to make the best fluffy pancakes.
First, you'll need one and a half cups of all-purpose flour. 
Add three and a half teaspoons of baking powder, a teaspoon of salt, and a tablespoon of sugar.
Whisk those dry ingredients together.
Now, make a hole in the middle and pour in one and a quarter cups of milk, one egg, and three tablespoons of melted butter.
Whisk it until it's nice and smooth.
Get your pan hot on medium-high heat with a little oil.
Scoop about a quarter cup of batter for each pancake.
When you see bubbles, flip it!
Cook until golden brown on both sides. This makes about 4 servings.
Prep takes about 10 minutes and cooking another 15. Enjoy!
"""

def mock_extract_recipe(text):
    # This simulates the Gemini 3 extraction logic
    print("--- Simulating Gemini 3 Extraction ---")
    recipe = {
        "title": "Best Fluffy Pancakes",
        "ingredients": [
            "1 1/2 cups all-purpose flour",
            "3 1/2 teaspoons baking powder",
            "1 teaspoon salt",
            "1 tablespoon sugar",
            "1 1/4 cups milk",
            "1 egg",
            "3 tablespoons butter, melted"
        ],
        "instructions": [
            "Whisk dry ingredients (flour, baking powder, salt, sugar) in a large bowl.",
            "Create a well in the center and add milk, egg, and melted butter.",
            "Mix until smooth.",
            "Heat a lightly oiled pan over medium-high heat.",
            "Pour 1/4 cup of batter per pancake.",
            "Flip when bubbles appear and cook until golden brown on both sides."
        ],
        "prep_time": "10 mins",
        "cook_time": "15 mins",
        "servings": "4 people"
    }
    return recipe

if __name__ == "__main__":
    print("Recipe Extractor Phase 1 Demo")
    print("Input Source: YouTube Transcript (Simulated)")
    
    recipe = mock_extract_recipe(SAMPLE_TRANSCRIPT)
    
    print("\n--- Extracted Structured JSON ---")
    print(json.dumps(recipe, indent=2))
    
    with open("demo_test_output.json", "w") as f:
        json.dump(recipe, f, indent=2)
    print("\nDemo output saved to demo_test_output.json")
