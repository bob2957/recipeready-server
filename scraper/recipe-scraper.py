import json
import random

import pint
import requests
from recipe_scrapers import scrape_me

from uploader import Uploader
from walmart_scraper import WalmartScraper, GroceryItem

start_id = 9
end_id = int(1e6 - 1)
parsed_recipes = []
parsed_recipes_file = "parsed.txt"
recipe_id = -1
empty_img = "https://static01.nyt.com/applications/cooking/d8ae0eb/assets/"
key_file = "../keys.json"
app_id = ""
app_key = ""

standard_units = [
    "gram",
    "centimeter",
    "milliliter",
    "square centimeter"
]

def ini():
    global app_id, app_key, parsed_recipes
    with open(key_file, "r") as File:
        keys = json.loads(File.read())
    app_id = keys["app_id"]
    app_key = keys["app_key"]
    with open(parsed_recipes_file, "w+") as File:
        for i in File:
            parsed_recipes.append(int(i))


def get_ingredients_details(ingredients):
    payload = {
        "ingr": ingredients
    }
    print("Making request...")
    r = requests.post(f"https://api.edamam.com/api/nutrition-details?app_id={app_id}&app_key={app_key}",
                      json=payload)
    print("Received response")
    if r.status_code != 200:
        print("API failed to get ingredients with status code " + str(r.status_code))
        exit(r.status_code)
    return r.json()


def standardize(quantity, unit):
    ureg = pint.UnitRegistry(system='SI')
    try:
        q = int(quantity) * getattr(ureg, unit)
    except pint.errors.UndefinedUnitError:
        return [quantity, unit]
    for u in standard_units:
        if q.check(getattr(ureg, u)):
            q.ito(u)
            break
    # noinspection PyStringFormat
    return ('{:~P}'.format(q)).split(" ")


def parse_ingredients(ingredients):
    parsed_ingredients = {}
    sc = WalmartScraper()
    for i in ingredients["ingredients"]:
        i = i["parsed"][0]
        print("Scraping walmart.ca/cp/groceries...")
        item: GroceryItem = sc.query(i["foodMatch"])
        if "measure" not in i:
            amount = [None, None]
        else:
            amount = standardize(i["quantity"], i["measure"])
        parsed_ingredients[i["foodMatch"]] = {
            "quantity": None if amount[0] is None else int(amount[0]),
            "unit": amount[1],
            "calories": i["nutrients"]["ENERC_KCAL"]["quantity"],
            "price": item.price,
            "price_per_unit": item.price_per_unit,
            "description": item.description,
            "image": item.image_url
        }
    return parsed_ingredients


def convert_to_json(scraper):
    ingredients_details = get_ingredients_details(scraper.ingredients())
    parse_ingredients(ingredients_details)
    print("Creating JSON object...")
    try:
        image = scraper.image() if empty_img in scraper.image() else None
    except AttributeError:
        image = None
    recipe_details = {
        "imglink": image,
        "name": scraper.title(),
        "preptime": scraper.total_time() if scraper.total_time != 0 else None,
        "ingredients": parse_ingredients(ingredients_details),
        "steps": scraper.instructions(),
        "yield": int(scraper.yields().split(" ")[0]),
        "source": "https://cooking.nytimes.com/recipes/" + str(recipe_id),
        "nutrients": scraper.nutrients(),
        "vegan": "VEGAN" in ingredients_details["healthLabels"],
        "vegetarian": "VEGETARIAN" in ingredients_details["healthLabels"],
        "no_tree_nuts": "TREE_NUT_FREE" in ingredients_details["healthLabels"],
        "no_peanuts": "PEANUT_FREE" in ingredients_details["healthLabels"],
        "no_dairy": "DAIRY_FREE" in ingredients_details["healthLabels"],
        "halal": "PORK_FREE" in ingredients_details["healthLabels"]
    }
    print("Created JSON object")
    return recipe_details


if __name__ == "__main__":
    ini()
    up = Uploader()
    # gets a valid recipe that is not used already
    while 1:
        recipe_id = random.randint(start_id, end_id)
        if recipe_id not in parsed_recipes:
            scraper = scrape_me("https://cooking.nytimes.com/recipes/" + str(recipe_id))
            # runs a check to see if the page is not empty
            try:
                if scraper.title() is None:
                    continue
            except TypeError:
                print("Skipping")
                continue
            print("Recipe found " + str(recipe_id), scraper.title())

            data = convert_to_json(scraper)
            parsed_recipes.append(recipe_id)
            print(f"Valid recipe {recipe_id}, sending to db...")
            up.push(data)

            with (open(parsed_recipes_file, "a")) as file:
                print(f"Writing to {parsed_recipes_file}...")
                for line in parsed_recipes:
                    file.write(str(line))
            break
