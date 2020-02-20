import requests
import re
from bs4 import BeautifulSoup


class RecipeFetcher:
    search_base_url = 'https://www.allrecipes.com/search/results/?wt=%s&sort=re'

    def search_recipes(self, keywords):
        search_url = self.search_base_url % (keywords.replace(' ', '+'))

        page_html = requests.get(search_url)
        page_graph = BeautifulSoup(page_html.content)

        return [recipe.a['href'] for recipe in \
                page_graph.find_all('div', {'class': 'grid-card-image-container'})]

    def scrape_recipe(self, recipe_url):
        '''
        Extracts the "Ingredients" , "Directions"
        '''
        results = {}
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
        results['ingredients'] =lis

        # lis.clear()
        # print(lis)
        for i in page_graph.find_all('span', {'class', "recipe-directions__list--item"}):
            # print(i)
            print(i.text)
            if i.text.strip():
                lis1.append(i.text.strip())
        results['directions'] =lis1
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
        results['nutrients'] =lis2

        print(results)
        return results


rf = RecipeFetcher()
meat_lasagna = rf.search_recipes('meat lasagna')[0]
print(meat_lasagna)
results=rf.scrape_recipe(meat_lasagna)

