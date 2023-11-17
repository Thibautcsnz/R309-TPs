def fichier(f):
# Ouverture du fichier avec with :
    with open('toto.txt', 'r') as f:
        for l in f:
            l = l.rstrip("\n\r")
            print(l)
def creation(f):
# Fonction qui créer un fichier txt (ici titi.txt)
    file = open(f, "x")
    file.write("Le fichier a bien été crée")

