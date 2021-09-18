import random
import json
from recipe_scrapers import scrape_me

start_id = 500
end_id = int(1e6 - 1)
used_recipes = []
scraper = ""
recipe_id = -1
empty_img = "https://images.media-allrecipes.com/images/79591.png"


def convert_to_json(scraper):
    ingredients = []
    nutrients = -1
    recipe_details = {
        "image": scraper.image if scraper.image != empty_img else 'null',
        "name": scraper.title(),
        "prep_time": scraper.total_time() if scraper.total_time != 0 else 'null',
        "ingredients": ingredients,
        "servings": scraper.yields().split(" ")[0],
        "link": "https://www.allrecipes.com/recipe/" + str(recipe_id),
        "nutrients": nutrients
        # TODO: Add dietary restrictions
    }
    # TODO: Find out where this goes
    json.dumps(recipe_details)


if __name__ == "__main__":
    # gets a valid recipe that is not used already
    while 1:
        try:
            recipe_id = random.randint(start_id, end_id)
            if recipe_id not in used_recipes:
                scraper = scrape_me("https://www.allrecipes.com/recipe/" + str(recipe_id))
                convert_to_json(scraper)
                break
        except TypeError:
            used_recipes.append(recipe_id)
