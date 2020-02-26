def scale(ing,factor,dir):
    fac=factor
    if "down" in dir:
        fac=float(1/factor)
    new_ingr=[]
    print(type(ing))
    for i in ing["ingredients"]:
        i["qty"]=i["qty"]*fac
        new_ingr.append(i)
    print("scaled:",new_ingr)
    return new_ingr