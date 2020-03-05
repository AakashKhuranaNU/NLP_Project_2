import requests
import re
from bs4 import BeautifulSoup
from fractions import Fraction
import nltk
from nltk.tokenize import sent_tokenize
import spacy
import string
import json
import random
# import transformations

nlp = spacy.load("en_core_web_sm")

measurement = ["cup", "cups", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "spoon", "cloves", "jars", "pound",
               "pounds", "pinch", "links", "link", "package", "can", "cans", "ounce", "ounces"]

# TODO: Add more primary cooking methods, including present tense of them (Ex: "grilling")
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

    def __init__(self, url):
        # Ingredients_Sentence stores each original ingredient before it was put into our data structure
        # Ingredients stores each ingredient and it's prep, qty, etc
        # Directions_Sentence stores each original direction step before it was tokenized and broken apart
        # Directions_Data stores each step as a key, and then the tokenized structure and all data assosciated with it
        # as the value
        self.results = {
            "ingredients_sentence": [],
            "ingredients": [],
            "directions_sentence": [],
            "directions_data": {}
        }
        self.url = url
        self.already_scraped = False

    def split_ingredient(self, val):
        val = val.replace("or to taste", "")
        val = val.replace("to taste", "")
        val = val.replace("or more as needed", "")
        val = val.replace("more if needed", "")
        val = val.replace(", cut in half across the grain", "")
        val = val.replace(", drained and pressed", "")
        val = val.replace(", drained and sliced into large chunks", "")
        val = val.replace(", drained", "")
        val = val.replace(", cubed", "")
        val = val.replace(", cut into 8 pieces", "")
        ing = {
            "prep": "",
            "qty": 0,
            "alt_qty": "",
            "unit": "",
            "ingredient": "",
            "json_obj": {}
        }
        qty = float(0)
        comma_splice = val.split(', ')
        sp = comma_splice[0].split()
        tag = nltk.pos_tag(sp)
        for i in tag:
            if "VB" in i[1]:
                ing["prep"] = i[0]
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

        if str == '':
            str = "Not Found"
        ing["ingredient"] = str.strip()
        ing["alt_qty"] = str1.strip()
        ing["qty"] = qty
        return ing

    def parse_directions(self):
        for r in self.results['directions_sentence']:
            # self.results['directions_data'][r] = {}
            for s in sent_tokenize(r):
                method = {'primary_method': [], 'secondary_method': [], 'tool': [], 'ingredients': []}
                doc = nlp(s.lower())
                for ing in self.results['ingredients']:
                    # print(ing)
                    if ing['ingredient'] in s.lower():
                        method['ingredients'].append(ing)
                    elif ing['json_obj'] != {}:
                        for related_name in ing['json_obj']['related_names']:
                            if related_name in s.lower():
                                method['ingredients'].append(ing)
                for token in doc:
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
                        if token.text.isalpha() or not float(Fraction(token.text)).is_integer():
                            continue
                        table = str.maketrans('', '', string.punctuation)
                        temp = [w.translate(table) for w in s.split()]
                        ind = temp.index(token.text)
                        if temp[ind + 1] in TIME:
                            method['time'] = [token.text, temp[ind + 1]]
                        elif temp[ind + 1] in TEMP:
                            method['temp'] = [token.text, temp[ind + 1], temp[ind + 2]]
                # self.results['directions_data'][r][s] = method
                self.results['directions_data'][s] = method

    # def search_recipes(self):
    #     search_url = self.url % (self.keywords.replace(' ', '+'))
    #
    #     page_html = requests.get(search_url)
    #     page_graph = BeautifulSoup(page_html.content)
    #
    #     return [recipe.a['href'] for recipe in \
    #             page_graph.find_all('div', {'class': 'grid-card-image-container'})]

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
        with open('meat_replacement.json') as f:
            foods = json.load(f)
            return foods

    def compare_to_db(self):
        foods = self.load_food_properties()
        for ingredient in self.results['ingredients']:
            for food_key, prop in foods.items():
                if prop['related_names']:
                    if ingredient['ingredient'] in prop['related_names']:
                        idx = self.results['ingredients'].index(ingredient)
                        self.results['ingredients'][idx]['json_obj'] = prop
                        break
                    else:
                        split_found = False
                        split_ingredient = ingredient['ingredient'].split()
                        if split_ingredient:
                            for split in split_ingredient:
                                if split in prop['related_names']:
                                    split_found = True
                                    idx = self.results['ingredients'].index(ingredient)
                                    self.results['ingredients'][idx]['json_obj'] = prop
                        if split_found is True:
                            break
                if food_key in ingredient['ingredient']:
                    idx = self.results['ingredients'].index(ingredient)
                    self.results['ingredients'][idx]['json_obj'] = prop
                    break

    def search_and_scrape(self):
        if self.already_scraped is False:
            self.scrape_recipe(self.url)
            self.already_scraped = True
        else:
            lis3 = []
            self.results['directions_data'] = {}
            for i in self.results['ingredients_sentence']:
                a = self.split_ingredient(i)
                lis3.append(a)
            self.results["ingredients"] = lis3
        self.compare_to_db()
        self.parse_directions()
        # print("\n DIRECTIONS_DATA: \n")
        # for k, v in self.results['directions_data'].items():
        #     print("{k}: {v}".format(k=k, v=v))
        #     print("\n")
        # print("\n DIRECTIONS_SENTENCE: \n")
        # print(self.results['directions_sentence'])
        # print("\n INGREDIENTS_SENTENCE: \n")
        # print(self.results['ingredients_sentence'])
        print("\n INGREDIENTS: \n")
        print(self.results['ingredients'])


# Class for transforming the given recipe
class TransformRecipe:
    # This entire init can have everything removed except for 'rf' and 'to_or_from_vegetarian' for now
    def __init__(self, url):
        self.transformed_recipe = {
            "ingredients": [],
            "directions": [],
            "nutrients": []
        }
        self.food_properties_found = []
        self.rf = RecipeFetcher(url=url)
        self.to_or_from_vegetarian = False

    @staticmethod
    # Loads our local DB
    def load_food_properties():
        with open('meat_replacement.json') as f:
            foods = json.load(f)
            return foods


    def transform_scale(self, dir):
        #TODO: change sentences
        print("PLEASE ENTER SCALING FRACTION:")

        scaling_factor = input()
        scaling_factor = float(scaling_factor)

        if "down" in dir:
            scaling_factor = float(1 / scaling_factor)
        # new_ingr = []
        ing = self.rf.results
        # print(type(ing))
        for i in ing["ingredients"]:
            i["qty"] = i["qty"] * scaling_factor


        # print(self.rf.results['ingredients'])
            # new_ingr.append(i)
        # print("scaled:", new_ingr)

        new_ingredients = {}
        # print(type(ing))

        # print(ing['directions_data'])
        for i in ing['directions_data']:
            val = ing["directions_data"][i]
            khaak = val['ingredients']
            for i in ing['ingredients']:
                for ak in khaak:
                    if i['ingredient'] == ak['ingredient']:
                        ratio = i['qty']/ ak['qty'] / scaling_factor
                        ak['qty'] = ratio * scaling_factor * i['qty']
                            # new_ingr['qty'] = n['qty']

        self.pretty_printer(substitutes=None)
            # new_ingr.append(i)
        # print("scaled:", new_ingr)


    def transform_cuisine(self):
        # TODO: random choice
        print("PLEASE CHOOSE ONE OF THE FOLLOWING CUISINES:")
        print("1: ITALIAN")
        print("2: MEXICAN")

        choice = input()
        if choice == '1':
            for s in self.rf.results['directions_data']:
                val = self.rf.results['directions_data'][s]
                ingr = val['ingredients']
                for ing in ingr:
                    if ing['ingredient'] in transformations.to_italian:
                        s = s.replace(ing['ingredient'], transformations.to_italian[ing['ingredient']][0])
                        ing['ingredient'] = transformations.to_italian[ing['ingredient']][0]

        if choice == '2':
            for s in self.rf.results['directions_data']:
                val = self.rf.results['directions_data'][s]
                ingr = val['ingredients']
                for ing in ingr:
                    if ing['ingredient'] in transformations.to_mexican:
                        s = s.replace(ing['ingredient'], transformations.to_italian[ing['ingredient']][0])
                        ing['ingredient'] = transformations.to_italian[ing['ingredient']][0]

    def transform_from_dict(self, change):
        for s in self.rf.results['directions_data']:
            val = self.rf.results['directions_data'][s]
            ingr = val['ingredients']
            for ing in ingr:
                if ing['ingredient'] in change:
                    s = s.replace(ing['ingredient'], change[ing['ingredient']])
                    ing['ingredient'] = change[ing['ingredient']]

        self.pretty_printer(substitutes=change)

    def verbosity(self):
        pass

    def convert(self, val):
        return str(val)

    def transform_health(self, diff):
        with open('similar.json') as f:
            data = json.load(f)
        dat = data
        with open('meat_replacement.json') as f:
            hel_meat = json.load(f)

        nutr_api = "https://api.edamam.com/api/nutrition-data?app_id=26fb2b38&app_key=bd164bbb96197716e0e8827cc0aaaf43&ingr="

        replace = {}
        for ing in self.rf.results["ingredients"]:
            mod_str = self.modifier(ing["ingredient"])
            unmod = mod_str + ""
            # print(mod_str.replace(" ", "_"))
            mod_str = mod_str.replace(" ", "_")
            # print("ingr", ing)
            if unmod in hel_meat:
                # print("mod", mod_str)
                # print("found", mod_str)
                search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + ing["ingredient"]
                # if no result found then used the modified one
                print("search_url", search_url)
                nut_html = requests.get(search_url)
                print("nut_html",nut_html)
                nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                # print("nutrition", nut_graph)
                print(type(self.convert(nut_graph)))
                cal = json.loads(self.convert(nut_graph))
                print("nutr", cal["calories"])
                low = cal["calories"]

                for i in hel_meat:
                    search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + i
                    print("search_url", search_url)
                    nut_html = requests.get(search_url)
                    nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                    print("nutrition", nut_graph)
                    cal = (json.loads(self.convert(nut_graph)))
                    print("nutr", type(cal["calories"]))
                    # print("check",i["primary_methods"])
                    # and pmc in hel_meat[i]["primary_methods"]
                    if diff == "toHealthy":
                        if (cal["calories"]) < low and cal["calories"] != 0:
                            print("lower found ", cal["calories"], " ", i)
                            replace[ing["ingredient"]] = i
                            break
                    else:
                        if (cal["calories"]) > low and cal["calories"] != 0:    # and pmc in hel_meat[i]["primary_methods"]:
                            print("upper found ", cal["calories"], " ", i)
                            replace[ing["ingredient"]] = i
                            break

            elif mod_str in dat:
                print("found", mod_str)
                search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + ing["ingredient"]
                # if no result found then used the modified one
                print("search_url", search_url)
                nut_html = requests.get(search_url)
                nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                print("nutrition", nut_graph)
                cal = (json.loads(self.convert(nut_graph)))
                print("nutr", cal["calories"])
                low = cal["calories"]
                for found in dat[mod_str]:
                    # v=""+ing['qty']
                    # print(type(v))
                    print("found", found)
                    found = found.replace("_", " ")
                    search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + found
                    print("search_url", search_url)
                    nut_html = requests.get(search_url)
                    nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                    print("nutrition", nut_graph)
                    cal = (json.loads(self.convert(nut_graph)))
                    print("nutr", type(cal["calories"]))
                    if diff == "toHealthy":
                        if (cal["calories"]) < low and cal["calories"] != 0:
                            print("lower found ", cal["calories"], " ", found)
                            replace[ing["ingredient"]] = found
                            break
                    else:
                        if (cal["calories"]) > low and cal["calories"] != 0:
                            print("lower found ", cal["calories"], " ", found)
                            replace[ing["ingredient"]] = found
                            break

        self.pretty_printer(substitutes=replace)

    def modifier(self, ing):
        HEALTHY_MODIFIER = ["lean", "extra-lean", "extra lean", "lowfat", "low-fat", "low fat", "low-calorie",
                            "low calorie", "diet"]

        BASE_MODIFIER = ["wheat"]

        SIZE_MODIFIER = ["large", "medium", "med", "small", "good-sized", "whole", "half", "halves"]

        TYPE_MODIFIER = ["dry", "dried", "ground", "crushed", "flaked", "frozen", "fresh"]

        ing = ing.strip(string.punctuation).lower()
        for t in TYPE_MODIFIER:
            if t in ing:
                ing = ing.replace(t, "")
        for h in HEALTHY_MODIFIER:
            if h in ing:
                ing = ing.replace(h, "")
        for s in SIZE_MODIFIER:
            if s in ing:
                ing = ing.replace(s, "")
        for b in BASE_MODIFIER:
            if b in ing:
                ing = ing.replace(b, "")
        ing = ing.strip()
        return ing

    def transform_ingredients(self, substitutes, foods_db):
        # Loop through original ingredient "sentence"
        for ingredient_sentence in self.rf.results['ingredients_sentence']:
            ingredient_sentence_idx = self.rf.results['ingredients_sentence'].index(ingredient_sentence)
            # Loop through the ingredients data which holds each ingredient with their prep, qty, etc
            for props in self.rf.results['ingredients']:
                ing = props['ingredient']
                # If the ingredient is in the dictionary of substitutes created from "transform_directions"
                if ing in ingredient_sentence and ing in substitutes:
                    # Grab ingredient name and unit
                    ingredient_name = props['ingredient']
                    ingredient_unit = props['unit']

                    # Grab the substitute ingredient name and unit
                    try:
                        sub_ingredient_name = substitutes[ing]
                        sub_ingredient_unit = foods_db[sub_ingredient_name]['unit']
                    except:
                        continue

                    # Replace the ingredient name for the sub ingredient name
                    transformed_ingredient_sentence = ingredient_sentence
                    transformed_ingredient_sentence = \
                        transformed_ingredient_sentence.replace(ingredient_name, sub_ingredient_name)

                    # If the unit of the ingredient is in the list of measurements
                    # Replace the unit for sub unit
                    if ingredient_unit in measurement:
                        transformed_ingredient_sentence = \
                            transformed_ingredient_sentence.replace(ingredient_unit, sub_ingredient_unit)
                        self.rf.results['ingredients_sentence'][ingredient_sentence_idx] = \
                            transformed_ingredient_sentence
                    # Else, split it and add between
                    # Note: This is mainly for structure of "2 eggs" to become "2 pound tofu"
                    else:
                        splitted = transformed_ingredient_sentence.split(' ')
                        count = 0
                        transformed_modify = ""
                        for split in splitted:
                            if count == 1:
                                transformed_modify += sub_ingredient_unit + " " + split + " "
                            else:
                                transformed_modify += split + " "
                            count += 1
                        self.rf.results['ingredients_sentence'][ingredient_sentence_idx] = transformed_modify

    def transform_directions(self):
        # Ex: substitutes = {"lean ground beef": "tofu"}
        substitutes = {}
        ingredient_related_names = {}
        foods = self.load_food_properties()
        # Loop through the parsed data (key: overall step, value: dictionaries of that step tokenized into each sentence
        # for direction, direction_tokens in self.rf.results['directions_data'].items():
            # print("\n")
            # print("Direction: {direction}".format(direction=direction))
            # print("\n")
            # print("Directions_Data: {d_data}".format(d_data=self.rf.results['directions_data']))
            # print("\n")
            # print("Directions_Sentence: {d_sentence}".format(d_sentence=self.rf.results['directions_sentence']))
            # print("\n")
            # print("Direction_Tokens: {direction_tokens}".format(direction_tokens=direction_tokens))
            # print("\n")
            # directions_idx = self.rf.results['directions_sentence'].index(direction)
            # Loop through each tokenized sentence (key: tokenized sentence, value: dictionaries of data found
            # such as primary_method, tool, ingredients, etc
        for tokenized_direction, props in self.rf.results['directions_data'].items():
            # print("Tokenized_Direction: {tokenized_direction}".format(tokenized_direction=tokenized_direction))
            # print("\n")
            # print("Props: {props}".format(props=props))
            if props['ingredients'] is not None:
                # Loop through all ingredients found within the tokenized sentence
                for ingredient in props['ingredients']:
                    # print(ingredient)
                    # If ingredient with a need for substitute was not already found
                    # and ingredient was found in our local DB
                    if ingredient['ingredient'] not in substitutes and ingredient['json_obj'] != {}:
                        ingr_data = ingredient['json_obj']
                        # print(ingr_data)
                        # Consider only substituting if it's meat
                        if ingr_data['food_category'] == 'meat' and self.to_or_from_vegetarian is True:
                            # If the meat in question has related names and it's not in the dictionary
                            # that stores the (key) meat substitute and (val) related names
                            if ingr_data['related_names'] != [] and \
                                    ingredient['ingredient'] not in ingredient_related_names:
                                ingredient_related_names[ingredient['ingredient']] = ingr_data['related_names']
                            substitute_ing = ""
                            # If no substitute was found with the same primary method, choose random substitute
                            if substitute_ing == "" and ingr_data['vegetarian_substitutes'] is not None:
                                substitute_ing = random.choice(ingr_data['vegetarian_substitutes'])
                            substitutes[ingredient['ingredient']] = substitute_ing
                        elif ingr_data['food_category'] != 'meat' and self.to_or_from_vegetarian is False:
                            # If the vegetarian ingredient in question has
                            # related names and it's not in the dictionary
                            # that stores the (key) meat and (val) related names
                            if ingr_data['related_names'] != [] and \
                                    ingredient['ingredient'] not in ingredient_related_names:
                                ingredient_related_names[ingredient['ingredient']] = ingr_data['related_names']
                            substitute_ing = ""
                            # If no substitute was found with the same primary method, choose random substitute
                            if substitute_ing == "" and ingr_data['vegetarian_substitutes'] is not None:
                                substitute_ing = random.choice(ingr_data['vegetarian_substitutes'])
                            substitutes[ingredient['ingredient']] = substitute_ing
        # Loop through the dictionary of all items that need to be substituted
        for direction_loop in self.rf.results['directions_sentence']:
            directions_idx = self.rf.results['directions_sentence'].index(direction_loop)
            for food, sub_food in substitutes.items():
                # Find the most relative name ("Ground Beef" versus just "Beef")
                sorted_related_names = self.most_relative_name(ingredient_related_names, food)
                # If there is a sorted list of related names
                if sorted_related_names:
                    for sorted_name in sorted_related_names:
                        alpha_only_sorted_name = sorted_name.replace(' ', '')
                        if sorted_name in direction_loop and alpha_only_sorted_name.isalpha():
                            direction_replaced = direction_loop.replace(sorted_name, sub_food)
                            self.rf.results['directions_sentence'][directions_idx] = direction_replaced
                            break
        # self.remove_common_properities(directions_idx=directions_idx)
        return substitutes, foods

    @staticmethod
    # This method is for ensuring that the correct full name is replaced
    # (Ex: "Ground Beef" becomes Tofu instead of "Ground Tofu")
    def most_relative_name(ingredient_related_names, ingredient):
        if ingredient_related_names[ingredient]:
            sorted_related_names = sorted(ingredient_related_names[ingredient], key=len, reverse=True)
            sorted_related_names.append('meat')
            # print(sorted_related_names)
            return sorted_related_names
        return []

    def remove_common_properities(self, directions_idx):
        if self.to_or_from_vegetarian:
            common_words = ["remove the grease"]
        else:
            common_words = ["Mix"]

        for common_word in common_words:
            if common_word in self.rf.results['directions_sentence'][directions_idx]:
                direction = self.rf.results['directions_sentence'][directions_idx]
                direction = direction.replace(common_word, "")
                self.rf.results['directions_sentence'][directions_idx] = direction

    def load_recipe(self):
        self.rf.search_and_scrape()
        print("\n INGREDIENTS: \n")
        for ingredient in self.rf.results['ingredients_sentence']:
            print(ingredient)
        print("\n DIRECTIONS: \n")
        for direction in self.rf.results['directions_sentence']:
            print(direction)


    # We parse directions before ingredients because we want to learn as much information as possible
    # Such as choosing a vegetarian substitute with the same cooking method
    def master_transform(self):
        # to_or_from_vegetarian needs to be marked True for meat -> vegetarian and False for opposite
        substitutes, foods_db = self.transform_directions()
        print(self.rf.results['directions_sentence'])
        self.transform_ingredients(substitutes=substitutes, foods_db=foods_db)
        self.pretty_printer(substitutes=substitutes)


    def pretty_printer(self, substitutes):
        if substitutes:
            print("\n Ingredient Changelog: \n")
            for ingr, sub in substitutes.items():
                print("{ingr}: {sub}".format(ingr=ingr, sub=sub))
        print("\n INGREDIENTS: \n")
        for ingredient in self.rf.results['ingredients_sentence']:
            print(ingredient)
        print("\n DIRECTIONS: \n")
        for direction in self.rf.results['directions_sentence']:
            print(direction)


def main():
    main_util()


def main_util():
    print("HI! PLEASE ENTER A RECIPE URL")
    user_url = input()
    transform = TransformRecipe(url=user_url)
    while True:
        transform.load_recipe()
        print("PLEASE ENTER ONE OF THE FOLLOWING CHOICES:")
        print("1: TRANSFORM TO NON-VEG")
        print("2: TRANSFORM TO VEG")
        print("3: TRANSFORM TO ANOTHER CUISINE")
        print("4: MAKE IT HEALTHY")
        print("5: MAKE IT UNHEALTHY")
        print("6: SCALE THE RECIPE UP")
        print("7: SCALE THE RECIPE DOWN")
        print("8: MAKE RECIPE VERBOSE")
        print("9: TRY ANOTHER RECIPE")
        print("10: EXIT")

        user_choice = input()
        user_choice = int(user_choice)
        if user_choice == 1:
            transform.to_or_from_vegetarian = False
            transform.master_transform()
        elif user_choice == 2:
            transform.to_or_from_vegetarian = True
            transform.master_transform()
        elif user_choice == 3:
            transform.transform_cuisine()
        elif user_choice == 4:
            transform.transform_health(diff='toHealthy')
        elif user_choice == 5:
            transform.transform_health(diff='toUnhealthy')
        elif user_choice == 6:
            transform.transform_scale(dir='up')
        elif user_choice == 7:
            transform.transform_scale(dir='down')
        elif user_choice == 8:
            transform.verbosity()
        elif user_choice == 9:
            print("HI! PLEASE ENTER A RECIPE URL")
            user_url = input()
            transform = TransformRecipe(url=user_url)
            transform.load_recipe()
        else:
            print("BON APPETIT :D")
            break


if __name__ == "__main__":
    main()

