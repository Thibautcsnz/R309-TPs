from exercice2 import *
#Fichier maintp2 qui est associé à l'Exercice2 des Exceptions de Fichiers
if __name__ == '__main__':
    try:
        f = "toto.txt"
        fichier(f)
        creation("titi.txt")

    except FileNotFoundError:
        print("Le fichier n'a pas été trouvé")

    except IOError:
        print("Le fichier ne peut pas être ouvert / lu")

    except FileExistsError:
        print("Le fichier existe déjà")

    except PermissionError:
        print("Vous n'avez pas la permission d'ouvrir le fichier")

    finally:
        print("Fin du programme")
