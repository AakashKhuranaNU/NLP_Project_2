import requests
import nltk
from fractions import Fraction
import re
from bs4 import BeautifulSoup


measurement=["cup","cups","tablespoon","tablespoons","teaspoon","teaspoons","spoon","cloves","jars","pound","pinch","links","link","package"]

class RecipeFetcher:
    search_base_url = 'https://www.allrecipes.com/search/results/?wt=%s&sort=re'



    def split_ingredient(self, val):
        val=val.replace("or to taste","")
        val=val.replace("to taste","")
        ing={}
        ing["prep"]=""
        ing["qty"]=0
        ing["alt_qty"]=""
        ing["unit"]=""
        ing["ingredient"]=""
        qty=float(0)
        sp=val.split()
        tag=nltk.pos_tag(sp)
        # print("tag",tag)
        for i in tag:
            if "VB" in i[1]:
                ing["prep"]=i[0]
        # print("splits",sp)
        str=""
        str1=""
        for j in sp:
            # print(j)
            if j in measurement:
                # print("measurement",j)
                ing["unit"]=j
            elif "(" in j or ")" in j:
                str1=str1+" "+j
            else :
                flag=0
                for i in j:
                    if i.isdigit() :
                        flag=1
                        break
                if flag==1:
                    # print("qty",j)
                    qty=qty+float(Fraction(j))
                elif j not in ing["prep"]:
                    str=str+" "+j

        ing["ingredient"]=str.strip()
        ing["alt_qty"]=str1.strip()
        ing["qty"]=qty
        print("ingr",ing)
        return ing

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
        lis3=[]
        for i in lis:
            a=self.split_ingredient(i)
            lis3.append(a)
        results["ingredients"]=lis3
        # lis.clear()
        # print(lis)
        for i in page_graph.find_all('span', {'class', "recipe-directions__list--item"}):
            # print(i)
            # print(i.text)
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

