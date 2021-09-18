import random
import json
import traceback

import requests
from recipe_scrapers import scrape_me

start_id = 500
end_id = int(1e6 - 1)
parsed_recipes = []
parsed_recipes_file = "parsed.txt"
recipe_id = -1
empty_img = "https://images.media-allrecipes.com/images/79591.png"
key_file = "keys.json"
app_id = ""
app_key = ""


def ini():
    global app_id, app_key
    with open(key_file, "r") as File:
        keys = json.loads(File.read())
    app_id = keys["app_id"]
    app_key = keys["app_key"]


def get_ingredients_details(ingredients):
    payload = {
        "ingr": ['1 pound uncooked spaghetti',
                 '6 cloves garlic, thinly sliced',
                 '½ cup olive oil',
                 '¼ teaspoon red pepper flakes, or to taste',
                 'salt and freshly ground black pepper to taste',
                 '¼ cup chopped fresh Italian parsley',
                 '1 cup finely grated Parmigiano-Reggiano cheese']
    }
    print("Making request...")
    r = requests.post(f"https://api.edamam.com/api/nutrition-details?app_id={app_id}&app_key={app_key}",
                      json=payload)
    print("Received response")
    if r.status_code != 200:
        print("API failed to get ingredients with status code " + str(r.status_code))
        exit(r.status_code)
    return r.json()


def parse_ingredients(ingredients):
    # TODO: add prices and image
    parsed_ingredients = {}
    for i in ingredients["ingredients"]:
        i = i["parsed"][0]
        if "measure" not in i:
            i["quantity"] = "null"
            i["measure"] = "null"
        parsed_ingredients[i["foodMatch"]] = {
            "quantity": i["quantity"],
            "unit": i["measure"],
            "calories": i["nutrients"]["ENERC_KCAL"]["quantity"]
        }
    return parsed_ingredients


def convert_to_json(scraper):
    ingredients_details = get_ingredients_details(scraper.ingredients())
    parse_ingredients(ingredients_details)
    print("Creating JSON object...")
    try:
        image = scraper.image() if scraper.image() != empty_img else 'null'
    except AttributeError:
        image = 'null'
    recipe_details = {
        "imglink": image,
        "name": scraper.title(),
        "prep_time": scraper.total_time() if scraper.total_time != 0 else 'null',
        "ingredients": parse_ingredients(ingredients_details),
        "servings": int(scraper.yields().split(" ")[0]),
        "link": "https://www.allrecipes.com/recipe/" + str(recipe_id),
        "nutrients": scraper.nutrients(),
        "vegan": "VEGAN" in ingredients_details["healthLabels"],
        "vegetarian": "VEGETARIAN" in ingredients_details["healthLabels"],
        "no_tree_nuts": "TREE_NUT_FREE" in ingredients_details["healthLabels"],
        "no_peanuts": "PEANUT_FREE" in ingredients_details["healthLabels"],
        "no_dairy": "DAIRY_FREE" in ingredients_details["healthLabels"],
        "halal": "PORK_FREE" in ingredients_details["healthLabels"]
    }
    print("Created JSON object")
    return json.dumps(recipe_details, indent=4)


if __name__ == "__main__":
    ini()
    # gets a valid recipe that is not used already
    while 1:
        try:
            recipe_id = random.randint(start_id, end_id)
            if recipe_id not in parsed_recipes:
                scraper = scrape_me("https://www.allrecipes.com/recipe/" + str(recipe_id))
                print("Recipe found " + str(recipe_id))
                scraper.title()  # runs a check to see if the page is not empty
                data = convert_to_json(scraper)
                with (open("data.json", "w")) as file:
                    file.write(data)
                parsed_recipes.append(recipe_id)
                print(f"Valid recipe {recipe_id}, sending to db...")
                with (open(parsed_recipes_file, "a")) as file:
                    print(f"Writing to {parsed_recipes_file}...")
                    for line in parsed_recipes:
                        file.write(str(line))
                break
        except TypeError as err:
            parsed_recipes.append(recipe_id)
