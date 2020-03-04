from nltk.tokenize import sent_tokenize, word_tokenize
import spacy
import string

nlp = spacy.load("en_core_web_sm")

ingredients = ['lasagna noodles', 'ground beef', 'garlic', 'garlic powder', 'oregano', 'salt',
               'black pepper', 'cottage cheese', 'eggs', 'parmesan cheese', 'tomato-basil pasta sauce',
               'mozzarella cheese']

recipe = ['Preheat oven to 350 degrees F (175 degrees C).',
          'Fill a large pot with lightly salted water and bring to a rolling boil over high heat. Once the water is boiling, add the lasagna noodles a few at a time, and return to a boil. Cook the pasta uncovered, stirring occasionally, until the pasta has cooked through, but is still firm to the bite, about 10 minutes. Remove the noodles to a plate.',
          'Place the ground beef into a skillet over medium heat, add the garlic, garlic powder, oregano, salt, and black pepper to the skillet. Cook the meat, chopping it into small chunks as it cooks, until no longer pink, about 10 minutes. Drain excess grease.',
          'In a bowl, mix the cottage cheese, eggs, and Parmesan cheese until thoroughly combined.',
          'Place 4 noodles side by side into the bottom of a 9x13-inch baking pan; top with a layer of the tomato-basil sauce, a layer of ground beef mixture, and a layer of the cottage cheese mixture. Repeat layers twice more, ending with a layer of sauce; sprinkle top with the mozzarella cheese. Cover the dish with aluminum foil.',
          'Bake in the preheated oven until the casserole is bubbling and the cheese has melted, about 30 minutes. Remove foil and bake until cheese has begun to brown, about 10 more minutes. Allow to stand at least 10 minutes before serving.']

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

for r in recipe:
    for s in sent_tokenize(r):
        print(s)
        method = {'primary_method': [], 'secondary_method': [], 'tool': []}
        ingr = {'name': []}
        doc = nlp(s.lower())
        for ing in ingredients:
            if ing in s.lower():
                ingr['name'].append(ing)
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
                else:
                    ingr['quantity'] = [token.text]
        print(method, ingr)
        print('***')