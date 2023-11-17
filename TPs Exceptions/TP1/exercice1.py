# Exercice 1 qui traite des exceptions avec la fonction divEntier (division Euclidienne)
def divEntier(x: int, y: int) -> int:
    if x < y:
        return 0
    else:
        x = x - y
        return divEntier(x, y) + 1