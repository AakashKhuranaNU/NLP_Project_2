import requests
import re
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
import json


# Class for Recipe Scraping
class RecipeFetcher:

    def __init__(self, url, keywords):
        self.results = {}
        self.url = url
        self.keywords = keywords

    # search_base_url = 'https://www.allrecipes.com/search/results/?wt=%s&sort=re'

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
        # results = {}
        lis=[]
        lis1=[]
        lis2=[]
        page_html = requests.get(recipe_url)
        page_graph = BeautifulSoup(page_html.content)

        # print(page_graph)
        for i in page_graph.find_all('span', {'class', "recipe-ingred_txt added"}):
            # print(i)
            print(i.text)
            lis.append(i.text)
        self.results['ingredients'] =lis

        # lis.clear()
        # print(lis)
        for i in page_graph.find_all('span', {'class', "recipe-directions__list--item"}):
            # print(i)
            print(i.text)
            if i.text.strip():
                lis1.append(i.text.strip())
        self.results['directions'] =lis1
        # Fill out this list comprehension and get each element's text
        #

        pattern = re.compile(r'(window.lazyModal\(\')(.*)\'\);')
        nutr_link=page_graph.find("script",text=pattern)

        nutr_link_url=pattern.search(nutr_link.text).group(2)
        page_html_nutr = requests.get(nutr_link_url)
        page_graph_nutr = BeautifulSoup(page_html_nutr.content)
        # print(page_graph_nutr)
        for i in page_graph_nutr.find_all('span', {'class', "nutrient-name"}):
            # print("Nutrients")
            # print(i.text)
            lis2.append(i.text)
        self.results['nutrients'] =lis2

        for k, v in self.results.items():
            print("{k}: {v}".format(k=k, v=v))
            print("\n")

    def search_and_scrape(self):
        food = self.search_recipes()[0]
        print(food)
        self.scrape_recipe(food)


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
class MeatVegetarian:
    def __init__(self, meat, type, sub_meats, primaryMethods, vegetarian_substitutes):
        self.type = type
        self.meat = meat
        self.sub_meats = sub_meats
        self.primaryMethods = primaryMethods
        self.vegetarian_substitutes = vegetarian_substitutes

    def print_food(self):
        print("Type: {type}, \nMeat_Type: {meat}, \nSub_Meats: {sub_meats}, "
              "\nPrimaryMethods: {primary_methods}, \nVegetarianSubstitutes: {vegetarian_subs}".
              format(type=self.type, meat=self.meat, sub_meats=self.sub_meats, primary_methods=self.primaryMethods,
                     vegetarian_subs=self.vegetarian_substitutes))


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

    def transform_ingredients(self):
        self.rf.search_and_scrape()
        foods = self.load_food_properties()
        for sentence in self.rf.results['ingredients']:
            substitute_found = False
            tokenized = word_tokenize(sentence.lower())
            for k, v in foods.items():
                if k in tokenized:
                    mv = MeatVegetarian(k, foods[k][0], foods[k][1], foods[k][2], foods[k][3])
                    # foods_properties.append(mv)
                    # TODO: Make it choose a random substitute
                    self.transformed_recipe['ingredients'].append(mv.vegetarian_substitutes[0])
                    substitute_found = True
            if not substitute_found:
                self.transformed_recipe['ingredients'].append(sentence)

    def transform_directions(self):
        foods = self.load_food_properties()
        for sentence in self.rf.results['directions']:
            # substitute_found = False
            tokenized = word_tokenize(sentence.lower())
            for k, v in foods.items():
                if k in tokenized:
                    mv = MeatVegetarian(k, foods[k][0], foods[k][1], foods[k][2], foods[k][3])
                    ind = tokenized.index(k)
                    tokenized[ind] = mv.vegetarian_substitutes[0]
                    # self.transformed_recipe['directions'].append(mv.vegetarian_substitutes[0])
            untokenized = TreebankWordDetokenizer().detokenize(tokenized)
            # if not substitute_found:
            self.transformed_recipe['directions'].append(untokenized)

    def master_transform(self):
        self.transform_ingredients()
        self.transform_directions()

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
    transform = TransformRecipe(url='https://www.allrecipes.com/search/results/?wt=%s&sort=re',
                                keywords='meat lasagna')
    transform.master_transform()
    transform.pretty_printer()


if __name__== "__main__":
    main()
