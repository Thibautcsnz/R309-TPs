if __name__ == '__maintp2__':
    try:
        f = open("toto.txt", "r")
        print(f.read())

    except FileNotFoundError:
        print("Le fichier n'a pas été trouvé")
