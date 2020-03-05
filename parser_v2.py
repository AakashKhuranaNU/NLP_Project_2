from __future__ import print_function
from nltk.stem.porter import *
import requests
import re
from bs4 import BeautifulSoup
from fractions import Fraction
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import spacy
import string
import json
import random
import transformations
import copy

nlp = spacy.load("en_core_web_sm")
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

HEALTHY_MODIFIER = ["lean", "extra-lean", "extra lean", "lowfat", "low-fat", "low fat", "low-calorie", "low calorie",
                    "diet", "vital", "fresh", "extra-virgin", "gluten", "wheat"]

OTHER_MODIFIER = ["heinz®", "oven-ready", "heinz"]

TYPES = ['meats', 'pasta', 'oils', 'sauces', 'vegetables', 'herbs', 'cheeses']

SIZE_MODIFIER = ["extra-large", "large", "medium", "med", "small", "good-sized", "whole", "half", "halves"]

TYPE_MODIFIER = ["dry", "dried", "ground", "crushed", "flaked", "frozen", "fresh", "grated", "diced", "peeled",
                 "finely"]

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
         'bread knife', 'browning tray', 'layer',
         'butter curler', 'cake and pie server', 'cheese knife', 'cheesecloth', 'knife', 'cherry pitter', 'chinoise',
         'cleaver', 'corkscrew', 'simmer',
         'cutting board', 'dough scraper', 'egg poacher', 'egg separator', 'egg slicer', 'egg timer', 'fillet knife',
         'fish scaler', 'fish slice',
         'flour sifter', 'food mill', 'funnel', 'garlic press', 'grapefruit knife', 'grater', 'gravy strainer', 'ladle',
         'lame', 'lemon reamer', 'casserole',
         'lemon squeezer', 'mandoline', 'mated colander pot', 'measuring cup', 'measuring spoon', 'grinder',
         'tenderiser', 'thermometer', 'melon baller',
         'mortar and pestle', 'nutcracker', 'nutmeg grater', 'oven glove', 'blender', 'fryer', 'pastry bush',
         'pastry wheel', 'peeler', 'pepper mill',
         'pizza cutter', 'masher', 'potato ricer', 'pot-holder', 'rolling pin', 'salt shaker', 'sieve', 'spoon', 'fork',
         'spatula', 'spider', 'tin opener', 'remove',
         'tongs', 'whisk', 'wooden spoon', 'zester', 'microwave', 'cylinder', 'aluminum foil', 'steamer',
         'broiler rack', 'grate', 'shallow glass dish', 'wok',
         'dish', 'broiler tray', 'slow cooker', 'plate']

TIME = ['seconds', 'minutes', 'hour']

TEMP = ['degrees']

TYPE_WORDS = []


measurement = ["cup", "cups", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "spoon", "cloves", "jars", "pound",
               "pounds", "pinch", "links", "link", "package", "can", "cans", "ounce", "ounces"]

# TODO: Add more primary cooking methods, including present tense of them (Ex: "grilling")



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
        adj = []
        ing = {
            "type": "",
            "prep": "",
            "qty": 0,
            "alt_qty": "",
            "unit": "",
            "ingredient": "",
            "descriptor": "",
            "json_obj": {}
        }
        qty = float(0)
        comma_splice = val.split(', ')
        sp = comma_splice[0].split()
        tag = nltk.pos_tag(sp)
        for i in tag:
            if "VBD" in i[1] or "VBN" in i[1]:
                ing["prep"] = i[0]
            if "JJ" in i[1]:
                adj.append(i[0])
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
        if adj:
            if adj[0] != str.strip() and "(" not in adj[0]:
                ing["descriptor"] = adj[0]
        return ing

    def closest(lst, K):
        return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

    def parse_directions(self):
        for i in range(len(self.results['ingredients'])):
            ing = self.results['ingredients'][i]['ingredient'].lower()
            for t in TYPE_MODIFIER:
                if t in ing:
                    ing = ing.replace(t, "")
            for h in HEALTHY_MODIFIER:
                if h in ing:
                    ing = ing.replace(h, "")
            for s in SIZE_MODIFIER:
                if s in ing:
                    ing = ing.replace(s, "")
            for b in OTHER_MODIFIER:
                if b in ing:
                    ing = ing.replace(b, "")
            ing = ing.strip()
            ing = ing.strip(string.punctuation)
            self.results['ingredients'][i]['ingredient'] = ing

        for i in self.results['ingredients']:
            if ' and' in i['ingredient']:
                rep = i['ingredient'].split(' and')
            elif ' or' in i['ingredient']:
                rep = i['ingredient'].split(' or')
            else:
                continue

            if rep[1] == "":
                i['ingredient'] = rep[0].strip()
                i['ingredient'] = i['ingredient'].strip(string.punctuation)
            else:
                i_new = copy.deepcopy(i)
                i['ingredient'] = rep[0].strip()
                i['ingredient'] = i['ingredient'].strip(string.punctuation)
                i_new['ingredient'] = rep[1].strip()
                i_new['ingredient'] = i_new['ingredient'].strip(string.punctuation)
                self.results['ingredients'].append(i_new)

        with open('food_reps.json') as f:
            foods = json.load(f)

        for ing in self.results['ingredients']:
            if 'juice' in ing['ingredient']:
                ing['type'] = 'juice'
            elif 'paste' in ing['ingredient']:
                ing['type'] = 'paste'
            elif 'sauce' in ing['ingredient']:
                ing['type'] = 'sauce'
            elif 'oil' in ing['ingredient'] or 'butter' in ing['ingredient']:
                ing['type'] = 'oil'
            else:
                for typ in TYPES:
                    if ing['type'] == "":
                        for food in foods[typ]:
                            if ing['ingredient'] in food.split(',')[0]:
                                ing['type'] = typ
                                break

        # print(self.results['ingrdients'])

        for r in self.results['directions_sentence']:
            for s in sent_tokenize(r):
                self.results['directions_data'][s] = {}
                # print(s)
                method = {'primary_method': [], 'secondary_method': [], 'tool': [], 'ingredients': []}
                ingr = []
                ing_ind = []
                doc = nlp(s.lower())
                for ing in self.results['ingredients']:
                    flag = 0
                    for word in nltk.word_tokenize(s.lower()):
                        # if lev.distance(ing['ingredient'], word) <= 2:
                        if stemmer.stem(ing['ingredient']) in stemmer.stem(word):
                            # print("1 ", ing['ingredient'], word)
                            method['ingredients'].append(ing)
                            ing_ind.append(nltk.word_tokenize(s.lower()).index(word))
                            # print(ing_ind)
                            flag += 1
                            break
#                     if flag == 0:
#                         if ing['json_obj'] != {}:
#                             for related_name in ing['json_obj']['related_names']:
#                                 if related_name in s.lower() and related_name:
#                                     method['ingredients'].append(ing)
#                                     ing_ind.append(nltk.word_tokenize(s.lower()).index(related_name))
#                                     flag += 1

                    if flag == 0:
                        tokenize = nltk.word_tokenize(ing['ingredient'])
                        # print(tokenize)
                        for i in range(len(tokenize)):
                            if tokenize[i] not in stop_words and tokenize[i] in nltk.word_tokenize(s.lower()):
                                # print("2 ", tokenize[i])
                                ingr.append(ing)
                                ing_ind.append(nltk.word_tokenize(s.lower()).index(tokenize[i]))
                                # print(ing_ind)
                                flag = 0
                                break

                for token in doc:
                    # print('token: {}, pos: {}'.format(token.text, token.pos_))
                    ind = 0
                    if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'VERB':
                        for t in TYPE_WORDS:
                            if t in token.text:
                                TYPES.append(t)
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
                        if token.text.isalpha():
                            if not float(Fraction(token.text)).is_integer():
                                continue
                        table = str.maketrans('', '', string.punctuation)
                        temp = [w.translate(table) for w in s.split()]
                        try:
                            ind = temp.index(token.text)
                            if temp[ind + 1] in TIME:
                                method['time'] = [token.text, temp[ind + 1]]
                            elif temp[ind + 1] in TEMP:
                                method['temp'] = [token.text, temp[ind + 1], temp[ind + 2]]
                        except:
                            continue
                # self.results['directions_data'][r][s] = method
                    elif token.pos_ == 'NUM' and 'inch' not in token.text and 'inches' not in token.text and 'in' not in token.text:
                        # print("NUM ", token.text)
                        table = str.maketrans('', '', '!"#$%&\'()*+,-.:;<=>?@[]^_`{|}~')
                        temp = [w.translate(table) for w in s.split(" ")]
                        ind = temp.index(token.text)
                        temp_ind = [i for i in ing_ind if i > ind]
                        if len(temp_ind) > 0:
                            fin_ind = min(temp_ind)
                        else:
                            fin_ind = -1
                        if re.search(r'\d', token.text) and not float(Fraction(token.text)).is_integer():
                            typ = s.split()[fin_ind].strip(string.punctuation)
                            for ing in ingr:
                                if typ in ing['type'] or typ in ing['ingredient']:
                                    ing['qty'] = float(Fraction(token.text))
                            continue
                        if temp[ind + 1] == 'L':
                            continue
                        if temp[ind + 1] in TIME:
                            method['time'] = [token.text, temp[ind + 1]]
                        elif (ind + 2) < len(temp) and temp[ind + 2] in TIME:
                            method['time'] = [token.text, temp[ind + 2]]
                        elif temp[ind + 1] in TEMP:
                            method['temp'] = [token.text, temp[ind + 1], temp[ind + 2]]
                        elif fin_ind >= 0 and re.search(r'\d', token.text):
                            # print(fin_ind)
                            typ = stemmer.stem(s.split()[fin_ind].strip(string.punctuation))
                            # print(typ)
                            for ing in ingr:
                                if typ in stemmer.stem(ing['ingredient']) or typ in stemmer.stem(ing['type']):
                                    ing['qty'] = float(token.text)
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
        # print("\n INGREDIENTS: \n")
        # print(self.results['ingredients'])


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

        for i in range(len(ing['ingredients_sentence'])):
            num = 0
            stri = ''
            for st in ing['ingredients_sentence'][i].split(' '):
                flag = 0
                for imp in st:
                    if imp.isdigit():
                        flag = 1

                if flag == 1 and flag == 1 and "(" not in st:
                    num += float(Fraction(st))
                    stri = stri + ' ' + st

            ing['ingredients_sentence'][i] = ing['ingredients_sentence'][i].replace(stri.strip(), str(num*scaling_factor))
        # print("ing ", ing['ingredients_sentence'])

        unstop = ["minute", "minutes", "to", "mins", "min", "minutes.","degree","degrees", "-"]
        tango_lis=[]
        for mango in self.rf.results['directions_sentence']:
            tango = mango
            st = ""
            sp = tango.split(" ")
            for sub in range(0, len(sp)):
                flag = 0
                sure = 0
                for j in sp[sub]:
                    if j.isdigit():
                        flag = 1
                        break
                if flag == 1 and "(" not in sp[sub] and "-" not in sp[sub] and "x" not in sp[sub] and sp[sub + 1] not in unstop:
                    val = str(float(Fraction(sp[sub])) * scaling_factor)
                else:
                    val = sp[sub]
                st = st + " " + val
            tango = st.strip()
            # print("tango scale", tango)
            temp = nltk.sent_tokenize(tango)
            temp1 = nltk.sent_tokenize(mango)
            for cheeku in range(0, len(temp)):
                h = self.rf.results["directions_data"][temp1[cheeku]]
                del self.rf.results['directions_data'][temp1[cheeku]]
                # print("h is", h)
                self.rf.results["directions_data"][temp[cheeku]] = h
            tango_lis.append(tango)
        self.rf.results['directions_sentence']=tango_lis

        # for sent in self.rf.results['directions_sentence']:
        #     idx = self.rf.results['directions_sentence'].index(sent)
        #     for r in nltk.sent_tokenize(sent):
        #         print("r ", r)
        #         ind = re.findall(r'\d', r)
        #         print("ind ", ind)
                # for index in ind:
                #     if r.split(' ')[ind]
                #     self.rf.results['directions_sentence'][idx]

        # print("ing ", self.rf.results['ingredients_sentence'])
        self.pretty_printer(substitutes=None)
            # new_ingr.append(i)
        # print("scaled:", new_ingr)


    def transform_cuisine(self):
        # TODO: random choice
        print("PLEASE CHOOSE ONE OF THE FOLLOWING CUISINES:")
        print("1: ITALIAN")
        print("2: MEXICAN")

        choice = input()
        substitutes = {}

        if choice == '1':
            for s in self.rf.results['directions_data']:
                val = self.rf.results['directions_data'][s]
                ingr = val['ingredients']
                for ing in ingr:
                    if ing['ingredient'] in transformations.to_italian:
                        rep_ing = random.choice(transformations.to_italian[ing['ingredient']])
                        substitutes[ing['ingredient']] = rep_ing

        if choice == '2':
            for s in self.rf.results['directions_data']:
                val = self.rf.results['directions_data'][s]
                ingr = val['ingredients']
                for ing in ingr:
                    if ing['ingredient'] in transformations.to_mexican:
                        rep_ing = random.choice(transformations.to_mexican[ing['ingredient']])
                        substitutes[ing['ingredient']] = rep_ing

        self.pretty_printer_new(substitutes=substitutes)
        self.pretty_printer(substitutes=substitutes)


    def pretty_printer_new(self, substitutes):
        new_dir = []
        new_ing = []
        # print("dir data")
        # print(self.rf.results['directions_data'])
        # print("new values")
        for mango in self.rf.results['directions_sentence']:
            tango = mango
            for sub in substitutes:
                if sub in mango:
                    tango = tango.replace(sub, substitutes[sub])
            if 1:
                temp = nltk.sent_tokenize(tango)
                temp1 = nltk.sent_tokenize(mango)
                for cheeku in range(0, len(temp)):
                    h = self.rf.results["directions_data"][temp1[cheeku]]
                    del self.rf.results['directions_data'][temp1[cheeku]]
                    # print("h is", h)
                    self.rf.results["directions_data"][temp[cheeku]] = h
            # print("tnago",tango,"   mango ",mango)
            # self.rf.results["directions_data"][tango]=self.rf.results["directions_data"][mango]
            # del self.rf.results['directions_data'][mango]
            new_dir.append(tango)
        # print(self.rf.results['directions_sentence'])
        self.rf.results["directions_sentence"] = new_dir
        # print(new_dir)
        # print(self.rf.results['directions_sentence'])
        # print("new dir")
        # print(self.rf.results["directions_data"])

        # for cheeku in self.rf.results["directions_data"]:

        for mango in self.rf.results['ingredients_sentence']:
            tango = mango
            for sub in substitutes:
                if sub in mango:
                    tango = tango.replace(sub, substitutes[sub])
            new_ing.append(tango)
        # print(self.rf.results['ingredients_sentence'])
        self.rf.results["ingredients_sentence"] = new_ing
        # print(new_ing)
        # print(self.rf.results['ingredients_sentence'])
        # print("new ing")

        for mandarin in self.rf.results['ingredients']:
            for sub in substitutes:
                if sub in mandarin["ingredient"]:
                    mandarin["ingredient"] = mandarin["ingredient"].replace(sub, substitutes[sub])

        # print("mandarin")
        # print(self.rf.results["ingredients"])
        # print(self.rf.results['directions_data'])
        # print(substitutes)


    # def transform_from_dict(self, change):
    #     for s in self.rf.results['directions_data']:
    #         val = self.rf.results['directions_data'][s]
    #         ingr = val['ingredients']
    #         for ing in ingr:
    #             if ing['ingredient'] in change:
    #                 s = s.replace(ing['ingredient'], change[ing['ingredient']])
    #                 ing['ingredient'] = change[ing['ingredient']]
    #
    #     self.pretty_printer(substitutes=change)

    def verbosity(self):
        print("\n INGREDIENTS: \n")
        for i in range(len(self.rf.results['ingredients_sentence'])):
            print(self.rf.results['ingredients_sentence'][i])
            print(self.rf.results['ingredients'][i])

        print("\n DIRECTIONS: \n")

        for i in range(len(self.rf.results['directions_sentence'])):
            print("STEP: ", self.rf.results['directions_sentence'][i])
            print('\n')
            temp = nltk.sent_tokenize(self.rf.results['directions_sentence'][i])
            count = 0
            count_max = len(temp)
            for j in range(count_max):
                print("SUBSTEP {}: {}".format(j+1, temp[j]))
                print(self.rf.results['directions_data'][temp[j]])
                print('\n')


    def convert(self, val):
        return str(val)

    def transform_health(self, diff):
        with open('similar.json') as f:
            data = json.load(f)
        dat = data
        with open('meat_replacement.json') as f:
            hel_meat = json.load(f)

        print("Transforming recipe...")
        nutr_api = "https://api.edamam.com/api/nutrition-data?app_id=c7972ed6&app_key=cfc832cb9cbd4cd95e0182ecef7eda4f&ingr="

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
                # print("search_url", search_url)
                nut_html = requests.get(search_url)
                # print("nut_html",nut_html)
                nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                # print("nutrition", nut_graph)
                # print(type(self.convert(nut_graph)))
                cal = json.loads(self.convert(nut_graph))
                # print("nutr", cal["calories"])
                low = cal["calories"]

                for i in hel_meat:
                    search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + i
                    # print("search_url", search_url)
                    nut_html = requests.get(search_url)
                    nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                    # print("nutrition", nut_graph)
                    cal = (json.loads(self.convert(nut_graph)))
                    # print("nutr", type(cal["calories"]))
                    # print("check",i["primary_methods"])
                    # and pmc in hel_meat[i]["primary_methods"]
                    if diff == "toHealthy":
                        if (cal["calories"]) < low and cal["calories"] != 0:
                            # print("lower found ", cal["calories"], " ", i)
                            replace[ing["ingredient"]] = i
                            break
                    else:
                        if (cal["calories"]) > low and cal["calories"] != 0:    # and pmc in hel_meat[i]["primary_methods"]:
                            # print("upper found ", cal["calories"], " ", i)
                            replace[ing["ingredient"]] = i
                            break

            elif mod_str in dat:
                # print("found", mod_str)
                search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + ing["ingredient"]
                # if no result found then used the modified one
                # print("search_url", search_url)
                nut_html = requests.get(search_url)
                nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                # print("nutrition", nut_graph)
                cal = (json.loads(self.convert(nut_graph)))
                # print("nutr", cal["calories"])
                low = cal["calories"]
                for found in dat[mod_str]:
                    # v=""+ing['qty']
                    # print(type(v))
                    # print("found", found)
                    found = found.replace("_", " ")
                    search_url = nutr_api + self.convert(ing['qty']) + " " + ing['unit'] + " " + found
                    # print("search_url", search_url)
                    nut_html = requests.get(search_url)
                    nut_graph = BeautifulSoup(nut_html.content, 'html.parser')
                    # print("nutrition", nut_graph)
                    cal = (json.loads(self.convert(nut_graph)))
                    # print("nutr", type(cal["calories"]))
                    if diff == "toHealthy":
                        if (cal["calories"]) < low and cal["calories"] != 0:
                            # print("lower found ", cal["calories"], " ", found)
                            replace[ing["ingredient"]] = found
                            break
                    else:
                        if (cal["calories"]) > low and cal["calories"] != 0:
                            # print("lower found ", cal["calories"], " ", found)
                            replace[ing["ingredient"]] = found
                            break

        self.pretty_printer_new(substitutes=replace)
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
            modified_direction = direction_loop
            for food, sub_food in substitutes.items():
                # Find the most relative name ("Ground Beef" versus just "Beef")
                sorted_related_names = self.most_relative_name(ingredient_related_names, food)
                # If there is a sorted list of related names
                if sorted_related_names:
                    for sorted_name in sorted_related_names:
                        alpha_only_sorted_name = sorted_name.replace(' ', '')
                        if sorted_name in modified_direction and alpha_only_sorted_name.isalpha():
                            modified_direction = modified_direction.replace(sorted_name, sub_food)
                            break
            self.rf.results['directions_sentence'][directions_idx] = modified_direction

        # self.remove_common_properities(directions_idx=directions_idx)

        # self.pretty_printer_new(substitutes=substitutes)
        u = list(self.rf.results['directions_data'].keys())
        count = 0
        for d_sent in self.rf.results['directions_sentence']:
            toks = nltk.sent_tokenize(d_sent)
            for sent in range(len(toks)):
                h = self.rf.results['directions_data'][u[count]]
                del self.rf.results['directions_data'][u[count]]
                self.rf.results['directions_data'][toks[sent]] = h
                count += 1
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
        # print(self.rf.results['directions_sentence'])
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
        count = 0
        for direction in self.rf.results['directions_sentence']:
            print("Step %s: %s" % (count,  direction))
            count += 1


def main():
    main_util()


def main_util():
    print("HI! PLEASE ENTER A RECIPE URL")
    user_url = input()
    transform = TransformRecipe(url=user_url)
    transform.load_recipe()
    while True:
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
            if transform.rf.already_scraped:
                transform.load_recipe()
            transform.master_transform()
        elif user_choice == 2:
            transform.to_or_from_vegetarian = True
            if transform.rf.already_scraped:
                transform.load_recipe()
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
        elif user_choice == 10:
            print("BON APPETIT :D")
            break
        else:
            print("PLEASE ENTER A VALID NUMBER")
            continue


if __name__ == "__main__":
    main()

