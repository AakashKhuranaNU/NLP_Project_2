import requests
import re
from bs4 import BeautifulSoup
from fractions import Fraction
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
import spacy
import string
import json
import random

nlp = spacy.load("en_core_web_sm")

measurement = ["cup", "cups", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "spoon", "cloves", "jars", "pound",
               "pinch", "links", "link", "package", "can", "cans", "ounce", "ounces"]

PRIMARY_COOKING_METHODS = ['bake', 'steam', 'grill', 'roast', 'boil', 'fry', 'barbeque', 'baste', 'broil', 'poach',
                           'freeze', 'cure', 'saute', 'cook']

SECONDARY_COOKING_METHODS = ['pour', 'toast', 'topped', 'combine', 'chop', 'grate', 'serve', 'cut', 'shake', 'mince',
                             'stir', 'mix', 'crush', 'squeeze', 'beat', 'blend', 'caramelize', 'dice', 'dust',
                             'glaze', 'knead', 'pare', 'shred', 'toss', 'whip', 'sprinkle', 'grease', 'arrange',
                             'microwave', 'coat', 'turning', 'preheat', 'cover',
                             'broil', 'marinate', 'brushing', 'slice', 'season', 'whisk', 'heat', 'drain', 'stirring']

TOOLS = ['pan', 'bowl', 'baster', 'saucepan', 'knife', 'oven', 'beanpot', 'chip pan', 'cookie sheet', 'cooking pot',
         'crepe pan', 'double boiler', 'doufeu',
         'dutch oven', 'food processor', 'frying pan', 'skillet', 'griddle', 'karahi', 'kettle', 'pan',
         'pressure cooker', 'ramekin', 'roasting pan',
         'roasting rack', 'saucepansauciersaute pan', 'splayed saute pan', 'souffle dish', 'springform pan', 'stockpot',
         'tajine', 'tube panwok',
         'wonder pot', 'pot', 'apple corer', 'apple cutter', 'baster', 'biscuit cutter', 'biscuit press', 'baking dish',
         'bread knife', 'browning tray',
         'butter curler', 'cake and pie server', 'cheese knife', 'cheesecloth', 'knife', 'cherry pitter', 'chinoise',
         'cleaver', 'corkscrew',
         'cutting board', 'dough scraper', 'egg poacher', 'egg separator', 'egg slicer', 'egg timer', 'fillet knife',
         'fish scaler', 'fish slice',
         'flour sifter', 'food mill', 'funnel', 'garlic press', 'grapefruit knife', 'grater', 'gravy strainer', 'ladle',
         'lame', 'lemon reamer',
         'lemon squeezer', 'mandoline', 'mated colander pot', 'measuring cup', 'measuring spoon', 'grinder',
         'tenderiser', 'thermometer', 'melon baller',
         'mortar and pestle', 'nutcracker', 'nutmeg grater', 'oven glove', 'blender', 'fryer', 'pastry bush',
         'pastry wheel', 'peeler', 'pepper mill',
         'pizza cutter', 'masher', 'potato ricer', 'pot-holder', 'rolling pin', 'salt shaker', 'sieve', 'spoon', 'fork',
         'spatula', 'spider', 'tin opener',
         'tongs', 'whisk', 'wooden spoon', 'zester', 'microwave', 'cylinder', 'aluminum foil', 'steamer',
         'broiler rack', 'grate', 'shallow glass dish', 'wok',
         'dish', 'broiler tray', 'slow cooker', 'plate']

TIME = ['seconds', 'minutes', 'hour']

TEMP = ['degrees']


class RecipeFetcher:
    # search_base_url = 'https://www.allrecipes.com/search/results/?wt=%s&sort=re'

    def __init__(self, url, keywords):
        self.results = {
            "ingredients": [],
            "directions_data": {},
            "ingredients_sentence": [],
            "directions_sentence": []
        }
        self.url = url
        self.keywords = keywords

    def split_ingredient(self, val):
        val = val.replace("or to taste", "")
        val = val.replace("to taste", "")
        val = val.replace("or more as needed", "")
        val = val.replace("more if needed", "")
        ing = {
            "prep": "",
            "qty": 0,
            "alt_qty": "",
            "unit": "",
            "ingredient": "",
            "json_obj": {}
        }
        qty = float(0)
        sp = val.split()
        tag = nltk.pos_tag(sp)
        # print("tag",tag)
        for i in tag:
            if "VB" in i[1]:
                ing["prep"] = i[0]
        # print("splits",sp)
        str = ""
        str1 = ""
        for j in sp:
            # print(j)
            if j in measurement:
                # print("measurement",j)
                ing["unit"] = j
            elif "(" in j or ")" in j:
                str1 = str1 + " " + j
            else:
                flag = 0
                for i in j:
                    if i.isdigit():
                        flag = 1
                        break
                if flag == 1:
                    # print("qty",j)
                    qty = qty + float(Fraction(j))
                elif j not in ing["prep"]:
                    str = str + " " + j

        ing["ingredient"] = str.strip()
        ing["alt_qty"] = str1.strip()
        ing["qty"] = qty
        # print("ingr",ing)
        return ing

    def parse_directions(self):
        for r in self.results['directions_sentence']:
            self.results['directions_data'][r] = {}
            for s in sent_tokenize(r):
                method = {'primary_method': [], 'secondary_method': [], 'tool': [], 'ingredients': []}
                # list of ingredients found
                # ingr = []
                # ingr = {'name': []}
                doc = nlp(s.lower())
                for ing in self.results['ingredients']:
                    if ing['ingredient'] in s.lower():
                        # print(ing)
                        method['ingredients'].append(ing)
                        # ingr.append(ing)
                    elif ing['json_obj'] != {}:
                        for related_name in ing['json_obj']['related_names']:
                            if related_name in s.lower():
                                method['ingredients'].append(ing)
                                # ingr.append(ing)
                for token in doc:
                    # print('token: {}, pos: {}'.format(token.text, token.pos_))
                    if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'VERB':
                        if token.lemma_ in PRIMARY_COOKING_METHODS:
                            if token.lemma_ not in method['primary_method']:
                                method['primary_method'].append(token.lemma_)
                        elif token.lemma_ in SECONDARY_COOKING_METHODS:
                            if token.lemma_ not in method['secondary_method']:
                                method['secondary_method'].append(token.lemma_)
                        elif token.lemma_ in TOOLS:
                            if token.lemma_ not in method['tool']:
                                method['tool'].append(token.lemma_)
                    elif token.pos_ == 'NUM' and 'inch' not in token.text:
                        table = str.maketrans('', '', string.punctuation)
                        temp = [w.translate(table) for w in s.split()]
                        # temp = s.strip(string.punctuation).lower().split()
                        # print("temp: ", temp)
                        ind = temp.index(token.text)
                        if temp[ind + 1] in TIME:
                            method['time'] = [token.text, temp[ind + 1]]
                        elif temp[ind + 1] in TEMP:
                            method['temp'] = [token.text, temp[ind + 1], temp[ind + 2]]
                        # else:
                        #     ingr['quantity'] = [token.text]
                self.results['directions_data'][r][s] = method
                # print(method)
                # print('***')

    def search_recipes(self):
        search_url = self.url % (self.keywords.replace(' ', '+'))

        page_html = requests.get(search_url)
        page_graph = BeautifulSoup(page_html.content)

        return [recipe.a['href'] for recipe in \
                page_graph.find_all('div', {'class': 'grid-card-image-container'})]

    def scrape_recipe(self, recipe_url):
        '''
        Extracts the "Ingredients" , "Directions"
        '''
        lis = []
        lis1 = []
        lis2 = []
        page_html = requests.get(recipe_url)
        page_graph = BeautifulSoup(page_html.content)

        for i in page_graph.find_all('span', {'class', "recipe-ingred_txt added"}):
            lis.append(i.text)
            self.results['ingredients_sentence'].append(i.text)
        lis3 = []
        for i in lis:
            a = self.split_ingredient(i)
            lis3.append(a)
        self.results["ingredients"] = lis3
        for i in page_graph.find_all('span', {'class', "recipe-directions__list--item"}):
            if i.text.strip():
                lis1.append(i.text.strip())
        self.results['directions_sentence'] = lis1

        pattern = re.compile(r'(window.lazyModal\(\')(.*)\'\);')
        nutr_link = page_graph.find("script", text=pattern)

        nutr_link_url = pattern.search(nutr_link.text).group(2)
        page_html_nutr = requests.get(nutr_link_url)
        page_graph_nutr = BeautifulSoup(page_html_nutr.content)
        for i in page_graph_nutr.find_all('span', {'class', "nutrient-name"}):
            lis2.append(i.text)
        self.results['nutrients'] = lis2

    @staticmethod
    def load_food_properties():
        with open('./data/food_properties.json') as f:
            foods = json.load(f)
            return foods

    def compare_to_db(self):
        foods = self.load_food_properties()
        for ingredient in self.results['ingredients']:
            for food_key, prop in foods.items():
                if food_key in ingredient['ingredient']:
                    idx = self.results['ingredients'].index(ingredient)
                    self.results['ingredients'][idx]['json_obj'] = prop
                    break

    def search_and_scrape(self):
        food = self.search_recipes()[0]
        self.scrape_recipe(food)
        self.compare_to_db()
        self.parse_directions()
        print("\n DIRECTIONS_DATA: \n")
        for k, v in self.results['directions_data'].items():
            print("{k}: {v}".format(k=k, v=v))
            print("\n")
        print("\n DIRECTIONS_SENTENCE: \n")
        print(self.results['directions_sentence'])
        print("\n INGREDIENTS_SENTENCE: \n")
        print(self.results['ingredients_sentence'])
        print("\n INGREDIENTS: \n")
        print(self.results['ingredients'])


"""
List of Vegetarian Substitutes:
{
Jackfruit: ["Pulled Pork", "Chicken", "Tuna"],
Aquafaba (This goes into making things like brownies and other baked goods): ["Egg Whites", "Frosting", "Mayo"],

"""

"""
JSON Data:
1. Create a list of substitutes for all types of meat
2. Create a list of primary cooking methods for each type of food (meat, substitutes, vegetables, etc)
3. Create a list of tools that is associated with each primary cooking method
4. Create a list of measurements associated with each food

"""

"""
Steps for coding:
1. Parse the ingredients
2. Look for any meat words (ground beef, pulled pork, etc)
3. Add the ingredients that don't belong in the meat category to a new list of ingredients along with
   ingredient replacements for meat (and it's measurement)
4. Also add the old ingredients to a temp_dict that will be used to parse directions. ({"ground beef": "vegan beef"})
5. Any directions that have meat, will be replaced with the substitute value along with it's primary cooking method.


"""

# Class for storing information regarding
"""
came_from = The properties of the ingredient that we are transforming from
ingredient_name = Name of the substitute ingredient
food_category = (Ex: "Meat", "Dairy" or "Breads")
primary_methods = (Ex: "Fry", "Boil") for the substitute ingredient
avg_calorie = Average Calorie for 1 cup of this ingredient


"""


class SubstituteFood:
    def __init__(self, came_from, substitute_ingredient_name, food_category, primary_methods, avg_calorie):
        self.came_from = came_from
        self.substitute_ingredient_name = substitute_ingredient_name
        self.food_category = food_category
        self.primary_methods = primary_methods
        self.avg_calorie = avg_calorie

    def print_food(self):
        print("Came_From: {came_from}, \nSubstitute_Ingredient_Name: {ingredient_name}, "
              "\nFood_Category: {food_category}, "
              "\nPrimary_Methods: {primary_methods}, \nAvg_Calorie: {avg_calorie}".
              format(came_from=self.came_from, ingredient_name=self.substitute_ingredient_name,
                     food_category=self.food_category, primary_methods=self.primary_methods,
                     avg_calorie=self.avg_calorie))


# Class for transforming the given recipe
class TransformRecipe:
    def __init__(self, url, keywords):
        self.transformed_recipe = {
            "ingredients": [],
            "directions": [],
            "nutrients": []
        }
        self.food_properties_found = []
        self.rf = RecipeFetcher(url=url, keywords=keywords)

    @staticmethod
    def load_food_properties():
        with open('./data/food_properties.json') as f:
            foods = json.load(f)
            return foods

    def transform_ingredients(self, substitutes, foods_db):
        for ingredient_sentence in self.rf.results['ingredients_sentence']:
            ingredient_sentence_idx = self.rf.results['ingredients_sentence'].index(ingredient_sentence)
            for props in self.rf.results['ingredients']:
                ing = props['ingredient']
                if ing in ingredient_sentence and ing in substitutes:
                    ingredient_name = props['ingredient']
                    ingredient_unit = props['unit']
                    sub_ingredient_name = substitutes[ing]
                    sub_ingredient_unit = foods_db[sub_ingredient_name]['unit']
                    transformed_ingredient_sentence = ingredient_sentence
                    transformed_ingredient_sentence = \
                        transformed_ingredient_sentence.replace(ingredient_name, sub_ingredient_name)
                    transformed_ingredient_sentence = \
                        transformed_ingredient_sentence.replace(ingredient_unit, sub_ingredient_unit)

                    self.rf.results['ingredients_sentence'][ingredient_sentence_idx] = transformed_ingredient_sentence
        print(self.rf.results['ingredients_sentence'])

    def transform_directions(self):
        # Ex: substitutes = {"lean ground beef": "tofu"}
        substitutes = {}
        ingredient_related_names = {}
        foods = self.load_food_properties()
        for direction, direction_tokens in self.rf.results['directions_data'].items():
            directions_idx = self.rf.results['directions_sentence'].index(direction)
            for tokenized_direction, props in direction_tokens.items():
                if props['ingredients'] is not None:
                    for ingredient in props['ingredients']:
                        if ingredient['ingredient'] not in substitutes and ingredient['json_obj'] != {}:
                            ingr_data = ingredient['json_obj']
                            if ingr_data['related_names'] != [] and \
                                    ingredient['ingredient'] not in ingredient_related_names:
                                ingredient_related_names[ingredient['ingredient']] = ingr_data['related_names']
                            substitute_ing = ""
                            for substitute in ingr_data['vegetarian_substitutes']:
                                if props['primary_method'] != []:
                                    if props['primary_method'][0] in foods[substitute]['primary_methods']:
                                        substitute_ing = substitute
                            if substitute_ing == "" and ingr_data['vegetarian_substitutes'] is not None:
                                substitute_ing = random.choice(ingr_data['vegetarian_substitutes'])
                            substitutes[ingredient['ingredient']] = substitute_ing
            for food, sub_food in substitutes.items():
                sorted_related_names = self.most_relative_name(ingredient_related_names, food)
                if sorted_related_names:
                    for sorted_name in sorted_related_names:
                        if sorted_name in self.rf.results['directions_sentence'][directions_idx]:
                            direction = self.rf.results['directions_sentence'][directions_idx]
                            direction = direction.replace(sorted_name, sub_food)
                            self.rf.results['directions_sentence'][directions_idx] = direction
                            break
        print(substitutes)
        print(self.rf.results['directions_sentence'])
        return substitutes, foods

    @staticmethod
    # This method is for ensuring that the correct full name is replaced
    # (Ex: "Ground Beef" becomes Tofu instead of "Ground Tofu")
    def most_relative_name(ingredient_related_names, ingredient):
        if ingredient_related_names[ingredient]:
            sorted_related_names = sorted(ingredient_related_names[ingredient], key=len, reverse=True)
            return sorted_related_names
        return []

    def master_transform(self):
        self.rf.search_and_scrape()
        substitutes, foods_db = self.transform_directions()
        self.transform_ingredients(substitutes=substitutes, foods_db=foods_db)

    def pretty_printer(self):
        for k, v in self.transformed_recipe.items():
            print("{k}: ".format(k=k))
            for x in v:
                print("{x}".format(x=x))
                print("\n")
            print("\n")


# TODO: Search for words before and after the found target word
# If it's a new word, remove the element at that indice (Ex: "ground beef" ->
# Remove "ground" and replace "beef" with "tofu"

# TODO: Have a list of flag words that you replace with the substitute
# (Ex: "cook the meat" -> "cook the tofu")
def main():
    # transform = TransformRecipe(url='https://www.allrecipes.com/search/results/?wt=%s&sort=re',
    #                             keywords='meat lasagna')
    transform = TransformRecipe(url="https://www.allrecipes.com/search/results/?wt=%s&sort=re",
                                keywords="sloppy joes")
    transform.master_transform()
    # transform.pretty_printer()


if __name__ == "__main__":
    main()

# TODO:
"""
1. Parse ingredients & directions and build dictionaries
2. 
"""
