# Test Partie 1 -- Question 3

import random
from datetime import datetime
import time

# Fonction pour générer une liste de symboles aléatoires
def generer_liste_symbole(taille_max):
    # Fonction locale pour générer un symbole aléatoire
    def generer_symbole():
        while True:
            code_point = random.randint(0x1F300, 0x1F9FF) 
            symbole = chr(code_point)
            return symbole
    
    # Générer une liste de symboles de taille aléatoire
    liste_symb = [generer_symbole() for _ in range(random.randint(5, taille_max))]
    return liste_symb

# Fonction pour générer un délai d'arrivée de paquet selon une distribution exponentielle (poisson équivalent)
def arrivee_paquet(lamb):
    return random.expovariate(lamb)

# Fonction pour générer une couleur aléatoire
def generer_couleur_aleatoire():
    return "#{:02x}{:02x}{:02x}".format(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# Classe représentant une source de paquets
class Source():
    def __init__(self, id_source, buffer, lamb):
        self.id_source = id_source
        self.taux_arrive = lamb
        self.buffer = buffer

    # Méthode pour générer un paquet
    def generer_paquet(self):
        paquet = generer_liste_symbole(30)
        paquet_id = random.randint(1, 1000000)
        print(f"Nouveau paquet généré par la source {self.id_source} : {paquet_id}")
        return Paquet(paquet_id, paquet, couleur=generer_couleur_aleatoire(), id_source=self.id_source)

    # Méthode pour générer un paquet et l'envoyer au buffer (si conditions respecté)
    def envoyer_paquet_buffer(self):
        paquet = self.generer_paquet()
        temps_attente = arrivee_paquet(self.taux_arrive)
        self.buffer.nombre_total_paquets += 1  
        if not self.buffer.arrivee_insertion_paquet(paquet):
            paquet.temps_arrive = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}"
            print("Paquet envoyé vers le Buffer.")
        else:
            print("Échec de l'envoi du paquet. Le buffer est plein.")
            self.buffer.ajout_paquets_perdu(paquet)
        time.sleep(temps_attente) 

# Classe représentant un buffer
class Buffer():
    def __init__(self, capacite):
        self.capacite = capacite
        self.file_attente = []
        self.paquets_perdu = []
        self.nombre_total_paquets = 0

    # Méthode pour gérer l'arrivée d'un paquet dans le buffer (inserer ou pas)
    def arrivee_insertion_paquet(self, paquet):
        if len(self.file_attente) < self.capacite:
            self.file_attente.append(paquet)
            return False
        else:
            print("Buffer plein. Le paquet est perdu.")
            self.nombre_total_paquets += 1  
            return True

    # Méthode pour retirer un paquet du buffer
    def retrait_paquet(self):
        if self.file_attente:
            paquet = self.file_attente.pop(0)
            paquet.temps_depart = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}" 
            print("Paquet retiré du buffer !!!!!")
            return paquet
        else:
            print("La file d'attente est vide. Echec du Retrait!")
            return None

    # Méthode pour ajouter un paquet perdu à la liste des paquets perdus
    def ajout_paquets_perdu(self, paquet):
        self.paquets_perdu.append(paquet)  

    # Méthode pour obtenir le nombre de paquets perdus
    def nombre_paquets_perdu(self):
        return len(self.paquets_perdu)

# Classe représentant un paquet
class Paquet():
    def __init__(self, paquet_id, paquet, couleur, id_source):
        self.paquet_id = paquet_id
        self.id_source = id_source
        self.taille = len(paquet)
        self.paquet = paquet
        self.temps_arrive = None
        self.temps_depart = None
        self.couleur = couleur
     
     
if __name__ == "__main__":
    # Création d'un buffer de taille 20
    buffer = Buffer(20)
    sources = []

    # Création de trois sources de paquets
    for i in range(3):
        source = Source(id_source=i+1, buffer=buffer, lamb=0.5)
        sources.append(source)

    # Envoi de paquets des sources vers le buffer pendant 10 itérations
    for _ in range(10):
        for source in sources:
            source.envoyer_paquet_buffer()
            time.sleep(1)  # Attente de 1 seconde entre chaque envoi
        buffer.retrait_paquet()  # Retrait d'un paquet du buffer