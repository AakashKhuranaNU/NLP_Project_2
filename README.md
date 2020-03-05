TEAM MEMBERS: Aakash Khurana, Irinel Bandas, Unnati Parekh

PACKAGES: 
The required packages are mentioned in the requirements.txt file and can be downloaded as follows:
```pip install -r requirements.txt```

ABOUT THE IMPLEMENTATION:
The internal structure used for the transformations is present in the repo as flowcharts with names: 'Recipe.pdf'.

We have implemented the following required tasks:
* To and from vegetarian 
* To and from healthy 
* Style of cuisine

And the following optional tasks:
* Additional Style of cuisine 
* Double the amount or cut it by half (Our implementation takes in a scaling factor so it can scale by any arbitrary ratio, not just double or half)

HOW TO RUN:

All the classes and related methods for the Recipe-Transformer are present in 'parser_v2.py' . Run the following command to interact with the Recipe-Transformer:
```python parser_v2.py```

The Recipe Transformer asks user to input a recipe URL and it runs the scraper module to scrape the ingredients, directions and nutrient information from the webpage. This information will then be displayed on the console.

Next the Recipe-Transformer prompts the user with the choices among the following:
1: TRANSFORM TO NON-VEG
2: TRANSFORM TO VEG
3: TRANSFORM TO ANOTHER CUISINE (asks for choices from Italian and Mexican)
4: MAKE IT HEALTHY
5: MAKE IT UNHEALTHY
6: SCALE THE RECIPE UP (asks for scaling factor)
7: SCALE THE RECIPE DOWN (asks for scaling factor)
8: MAKE RECIPE VERBOSE (shows the internal structure used for the recipe and the ingredients)
9: TRY ANOTHER RECIPE
10: EXIT
