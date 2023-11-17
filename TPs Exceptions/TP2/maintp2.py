from exercice2 import *
# Fichier maintp2 qui est associé à l'Exercice2 des Exceptions de Fichiers
if __name__ == '__main__':
    try:
        f = "toto.txt"
        fichier(f)
        creation("titi.txt")
    # Exception relative au fichier inexistant
    except FileNotFoundError:
        print("Le fichier n'a pas été trouvé")
    # Exception relative au fichier ne pouvant être ouvert (problème écriture / lecture)
    except IOError:
        print("Le fichier ne peut pas être ouvert / lu")
    # Exception relative au fait que le fichier existe déjà et qu'il ne peut pas être réécrit)
    except FileExistsError:
        print("Le fichier existe déjà")
    # Exception relative aux permissions du fichier
    except PermissionError:
        print("Vous n'avez pas la permission d'ouvrir le fichier")

    finally:
        print("Fin du programme")
