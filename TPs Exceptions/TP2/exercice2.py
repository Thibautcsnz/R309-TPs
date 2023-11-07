def fichier(f):
    #file = open(f, "r")
    #print(file.read())
    with open('toto.txt', 'r') as f:
        for l in f:
            l = l.rstrip("\n\r")
            print(l)
def creation(f):
    file = open(f, "x")
    file.write("Le fichier a bien été crée")

