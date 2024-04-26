import tkinter as tk
from tkinter import ttk
import random
from datetime import datetime

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
    def __init__(self, id_source, buffer, app, lamb, mode_retrait):
        self.id_source = id_source
        self.buffer = buffer
        self.app = app
        self.taux_arrive = lamb
        self.mode_retrait = mode_retrait
        self.couleur = generer_couleur_aleatoire()
        self.nombre_paquets_genere = 0
        self.nombre_paquets_perdu = 0
        self.temps_dernier_retrait = datetime.now()
        self.temps_attente_moyen = 0
        self.total_temps_attente = 0
        self.nombre_retraits_effectues = 0

    # Méthode pour générer un paquet de symboles avec un ID propre à lui meme
    def generer_paquet(self):
        paquet = generer_liste_symbole(30)
        paquet_id = random.randint(1, 1000000)
        print(f"Nouveau paquet généré par la source {self.id_source} : {paquet_id}")
        self.paquet = paquet
        self.nombre_paquets_genere += 1
        return Paquet(paquet_id, paquet, couleur=self.couleur, id_source=self.id_source)

    # Méthode pour générer un paquet et l'envoyer au buffer (si conditions respecté)
    def envoyer_paquet_buffer(self):
        paquet = self.generer_paquet()
        temps_attente = arrivee_paquet(self.taux_arrive)
        if not self.buffer.arrivee_insertion_paquet(paquet):
            paquet.temps_arrive = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}"
            print("Paquet envoyé vers le Buffer.")
        else:
            self.buffer.ajout_paquets_perdu(paquet)
            self.nombre_paquets_perdu += 1
            print("Échec de l'envoi du paquet. Le buffer est plein.")
        # Acutalisation de l'interface avec les données actuel
        self.app.actualiser_affichage()
        self.calculer_taux_perdu()
        # Planifier l'envoi du prochain paquet après le temps d'attente
        self.app.after(int(temps_attente * 1000), self.envoyer_paquet_buffer)

    # Méthode pour générer les widgets nécessaires pour une source
    def creer_buffer_canvas(self):
        self.buffer_canvas = tk.Canvas(self.app.cadre_buffer, bg="lightgray", yscrollcommand=self.app.scrollbar_buffer_y.set, width=200)
        self.buffer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.nom_label = ttk.Label(self.buffer_canvas, text=f"Source {self.id_source} Buffer", relief=tk.SUNKEN)
        self.nom_label.pack()
        self.taux_perdu_label = ttk.Label(self.buffer_canvas, text="Taux de paquets perdus : 00.00%", relief=tk.SUNKEN)
        self.taux_perdu_label.pack()
        self.taux_attente_label = ttk.Label(self.buffer_canvas, text="Taux d'attente moyen : 00.0s", relief=tk.SUNKEN)
        self.taux_attente_label.pack()
        self.scrollbar_buffer_y = tk.Scrollbar(self.buffer_canvas, orient="vertical", command=self.buffer_canvas.yview)
        self.scrollbar_buffer_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.buffer_canvas.configure(yscrollcommand=self.scrollbar_buffer_y.set)

    # Méthode pour générer le taux de paquet moyen perdus d'un buffer
    def calculer_taux_perdu(self):
        if self.nombre_paquets_genere > 0:
            taux_perdu = (self.nombre_paquets_perdu / self.nombre_paquets_genere) * 100
            integer_part = int(taux_perdu)
            decimal_part = (taux_perdu - integer_part) * 100
            self.taux_perdu_label.config(text="Taux de paquets perdus : {:02.0f}.{:02.0f}%".format(integer_part, decimal_part))

    # Méthode pour générer le taux d'attente moyen d'un buffer (Ceux des sources)
    def calculer_taux_attente_moyen(self, temps_de_retrait):
        temps_actuel = datetime.now()
        intervalle_temps = (temps_actuel - self.temps_dernier_retrait).total_seconds()
        self.temps_dernier_retrait = temps_actuel
        self.total_temps_attente += intervalle_temps
        self.nombre_retraits_effectues += 1
        if self.nombre_retraits_effectues > 0:
            self.temps_attente_moyen = self.total_temps_attente / self.nombre_retraits_effectues
            formatted_attente = "{:04.1f}s".format(self.temps_attente_moyen)
            self.taux_attente_label.config(text=f"Taux d'attente moyen : {formatted_attente}")

class Buffer():
    def __init__(self, capacite, app):
        self.capacite = capacite
        self.file_attente = []
        self.paquets_perdu = []
        self.lien = []
        self.nombre_total_paquets = 0
        self.app = app

    # Méthode pour générer le taux d'attente moyen du Buffer principal
    def taux_perdu_buffer_principal(self):
        if self.nombre_total_paquets > 0:
            taux_perdu = (len(self.paquets_perdu) / self.nombre_total_paquets) * 100
            integer_part = int(taux_perdu)
            decimal_part = (taux_perdu - integer_part) * 100
            self.app.label_taux_perdu_principal.config(text="Taux de paquets perdus : {:02.0f}.{:02.0f}%".format(integer_part, decimal_part))

    # Méthode pour gérer l'arrivée d'un paquet dans le buffer (inserer ou pas)
    def arrivee_insertion_paquet(self, paquet):
        if len(self.file_attente) < self.capacite:
            self.file_attente.append(paquet)
            return False
        else:
            print("Buffer plein. Le paquet est perdu.")
            return True

    # Méthode pour ajouter un paquet perdu à la liste des paquets perdus
    def ajout_paquets_perdu(self, paquet):
        self.paquets_perdu.append(paquet)

    # Méthode pour transmettre un paquet du buffer vers le lien
    def retrait_paquet(self):
        if self.file_attente:
            paquet = self.file_attente.pop(0)
            paquet.temps_depart = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}" # enregistrer le temps de départ
            return paquet
        else:
            print("La file d'attente est vide. Echec du Retrait!")
            return None

    # Méthode pour transmettre un paquet du buffer vers le lien
    def transmission(self, paquet):
        self.lien.append(paquet)

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
        self.temps_depart_buffer = None
        self.couleur = couleur


class Configuration(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Configuration de la simulation")
        self.geometry("575x600")

        self.parent = parent
        self.sources_lambda_entrer = []
        self.sources_lambda_label = []

        self.label_sources = ttk.Label(self, text="Nombre sources:", background= "cyan")
        self.label_sources.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.sources_var = tk.IntVar(value=4)
        self.entrer_sources = ttk.Entry(self, textvariable=self.sources_var)
        self.entrer_sources.grid(row=0, column=1, padx=5, pady=5)

        self.bouton_valider_sources = ttk.Button(self, text="Valider Nombre Sources", command=self.afficher_champs_lambda)
        self.bouton_valider_sources.grid(row=0, column=2, padx=5, pady=5)

        self.bouton_valider = ttk.Button(self, text="Valider La Config", command=self.valider_configuration)
        self.bouton_valider.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        self.label_delai_retrait = ttk.Label(self, text="Délai de retrait (secondes):", background= "green")
        self.label_delai_retrait.grid(row=2, column=0, padx=5, pady=5, sticky="e")

        self.delai_retrait_var = tk.DoubleVar(value=0.1)
        self.entrer_delai_retrait = ttk.Entry(self, textvariable=self.delai_retrait_var)
        self.entrer_delai_retrait.grid(row=2, column=1, padx=5, pady=5)

        self.label_capacite_buffer = ttk.Label(self, text="Capacité du buffer:", background= "red")
        self.label_capacite_buffer.grid(row=3, column=0, padx=5, pady=5, sticky="e")

        self.capacite_buffer_var = tk.IntVar(value=20)
        self.entrer_capacite_buffer = ttk.Entry(self, textvariable=self.capacite_buffer_var)
        self.entrer_capacite_buffer.grid(row=3, column=1, padx=5, pady=5)

        self.label_mode_retrait = ttk.Label(self, text="Mode de retrait:", background= "orange")
        self.label_mode_retrait.grid(row=4, column=0, padx=5, pady=5, sticky="e")

        self.mode_retrait_var = tk.StringVar(value="aleatoire")
        self.mode_retrait_aleatoire = ttk.Radiobutton(self, text="Aléatoire", variable=self.mode_retrait_var, value="aleatoire")
        self.mode_retrait_aleatoire.grid(row=4, column=1, padx=5, pady=5)

        self.mode_retrait_tour_de_role = ttk.Radiobutton(self, text="Tour de rôle", variable=self.mode_retrait_var, value="tour_de_role")
        self.mode_retrait_tour_de_role.grid(row=4, column=2, padx=5, pady=5)

        self.mode_retrait_file_max_paquets = ttk.Radiobutton(self, text="Max de paquets", variable=self.mode_retrait_var, value="file_max_paquets")
        self.mode_retrait_file_max_paquets.grid(row=4, column=3, padx=5, pady=5)

    # Méthode pour afficher les champs lambda pour chaque source
    def afficher_champs_lambda(self):
        sources = self.sources_var.get()
        # Nettoyer les entrées lambda existantes
        for entry in self.sources_lambda_entrer:
            entry.destroy()
        for label in self.sources_lambda_label:
            label.destroy()
        self.sources_lambda_entrer = []
        self.sources_lambda_label = []
        # Créer des champs lambda pour chaque source
        for i in range(sources):
            label_lambda = ttk.Label(self, text=f"Lambda Source {i+1}:")
            label_lambda.grid(row=i+6, column=0, padx=5, pady=5, sticky="e")
            self.sources_lambda_label.append(label_lambda)

            lambda_var = tk.DoubleVar(value=0.5)
            entrer_lambda = ttk.Entry(self, textvariable=lambda_var)
            entrer_lambda.grid(row=i+6, column=1, padx=5, pady=5)
            self.bouton_valider.grid(row=i+8, column=0, columnspan=3, padx=5, pady=15)
            self.sources_lambda_entrer.append(entrer_lambda)

    # Méthode pour valider la configuration de la simulation
    def valider_configuration(self):
        lambda_values = [entry.get() for entry in self.sources_lambda_entrer]
        delai_retrait = self.delai_retrait_var.get()
        capacite_buffer = self.capacite_buffer_var.get()
        mode_retrait = self.mode_retrait_var.get()
        self.parent.configurer_simulation(lambda_values, delai_retrait, capacite_buffer, mode_retrait)
        self.destroy()


class Reseau():
    def __init__(self, lambdas, delai_retrait, capacite_buffer, mode_retrait, app):
        self.app = app
        self.buffer_principal = Buffer(capacite_buffer, app = self.app)
        self.sources = []
        self.buffers = []
        self.mode_retrait = mode_retrait
        self.indice = 0
        self.delai_coef_retrait = delai_retrait
        for i, lamb in enumerate(lambdas):
            buffer_source = Buffer(capacite_buffer, app = self.app)
            source = Source(id_source=i+1, buffer=buffer_source, app=None, lamb=float(lamb), mode_retrait=mode_retrait)
            self.sources.append(source)
            self.buffers.append(buffer_source)

    # Méthode pour lancer la simulation
    def lancer_simulation(self):
        for source in self.sources:
            source.envoyer_paquet_buffer()

    # Méthode pour démarrer les retraits de paquets selon le mode de retrait choisi
    def demarrer_retraits(self):
        if self.mode_retrait == "aleatoire":
            self.app.after(1000, self.effectuer_retrait_aleatoire)
        elif self.mode_retrait == "tour_de_role":
            self.app.after(1000, self.effectuer_retrait_tour_de_role)
        elif self.mode_retrait == "file_max_paquets":
            self.app.after(1000, self.effectuer_retrait_max)
    
    # Méthode pour effectuer un retrait de paquet de manière aléatoire (parmi les sources)
    def effectuer_retrait_aleatoire(self):
        source_choisie = random.choice(self.sources)
        if source_choisie.buffer.file_attente:
            paquet_choisi = source_choisie.buffer.file_attente.pop(0)
            paquet_choisi.temps_depart_buffer = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}"
            temps_attente = paquet_choisi.taille * self.delai_coef_retrait
            source_choisie.calculer_taux_attente_moyen(temps_attente)
            if len(self.buffer_principal.file_attente) < self.buffer_principal.capacite:
                self.buffer_principal.file_attente.append(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.actualiser_affichage()
                self.app.after(int(1000* temps_attente), self.effectuer_retrait_aleatoire)
            else:
                self.buffer_principal.ajout_paquets_perdu(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.after(1000, self.effectuer_retrait_aleatoire)

    # Méthode pour effectuer un retrait de paquet du buffer ayant le plus de paquets (parmi les sources)
    def effectuer_retrait_max(self):
        if any(buffer.file_attente for buffer in self.buffers):  
            buffer_choisi = max(self.buffers, key=lambda buffer: len(buffer.file_attente))
            paquet_choisi = buffer_choisi.file_attente.pop(0)
            paquet_choisi.temps_depart_buffer = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}"
            temps_attente = paquet_choisi.taille * self.delai_coef_retrait

            indice_buffer_choisi = self.buffers.index(buffer_choisi)
            self.sources[indice_buffer_choisi].calculer_taux_attente_moyen(temps_attente)

            if len(self.buffer_principal.file_attente) < self.buffer_principal.capacite:
                self.buffer_principal.file_attente.append(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.actualiser_affichage()
                self.app.after(int(1000* temps_attente), self.effectuer_retrait_max)
            else:
                self.buffer_principal.ajout_paquets_perdu(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.after(1000, self.effectuer_retrait_max)

    # Méthode pour effectuer des retraits de paquets en tournant entre chaque source    
    def effectuer_retrait_tour_de_role(self):
        source_choisie = self.sources[self.indice]
        self.indice = (self.indice + 1) % len(self.sources)
        if source_choisie.buffer.file_attente:
            paquet_choisi = source_choisie.buffer.file_attente.pop(0)
            paquet_choisi.temps_depart_buffer = f"{datetime.now().hour}.{datetime.now().minute}.{datetime.now().second}"
            temps_attente = paquet_choisi.taille * self.delai_coef_retrait
            source_choisie.calculer_taux_attente_moyen(temps_attente)
            if len(self.buffer_principal.file_attente) < self.buffer_principal.capacite:
                self.buffer_principal.file_attente.append(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.actualiser_affichage()
                self.app.after(int(1000* temps_attente), self.effectuer_retrait_tour_de_role)
            else:
                self.buffer_principal.ajout_paquets_perdu(paquet_choisi)
                self.buffer_principal.nombre_total_paquets +=1
                self.app.after(1000, self.effectuer_retrait_tour_de_role)
        
    # Méthode pour retirer périodiquement des paquets du buffer principal
    def retrait_periodique_paquet(self):
        if self.buffer_principal.file_attente:
            paquet = self.buffer_principal.retrait_paquet()  
            if paquet:
                temps_attente = paquet.taille * self.delai_coef_retrait  
                self.buffer_principal.transmission(paquet)  
                self.app.actualiser_affichage()
                self.app.after(int(temps_attente * 2500), self.retrait_periodique_paquet)  
        else:
            self.app.after(2500, self.retrait_periodique_paquet)

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulation de buffer")

        self.attributes("-fullscreen", True)

        self.cadre_buffer = ttk.Frame(self)
        self.cadre_buffer.pack(fill=tk.BOTH, expand=True)

        self.titre_buffer = ttk.Label(self.cadre_buffer, text="Buffer", style="Titre.TLabel")
        self.titre_buffer.pack()

        self.label_taux_perdu_principal = ttk.Label(self.cadre_buffer, text="Taux de paquets perdus du buffer principal: 00.00%", style="Info.TLabel")
        self.label_taux_perdu_principal.pack(pady=10)

        self.scrollbar_buffer_y = tk.Scrollbar(self.cadre_buffer, orient="vertical")

        self.canvas_buffer = tk.Canvas(self.cadre_buffer, bg="lightgray", yscrollcommand=self.scrollbar_buffer_y.set)
        self.canvas_buffer.pack(side=tk.TOP, fill=tk.BOTH)
        self.scrollbar_buffer_y.config(command=self.canvas_buffer.yview)

        self.menu = Configuration(self)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Titre.TLabel", foreground="white", background="black", font=("Helvetica", 14, "bold"))
        self.style.configure("Info.TLabel", foreground="red", background="white", font=("Helvetica", 12))

        self.menu.transient(self)
        self.menu.grab_set()
        self.wait_window(self.menu)

    # Méthode pour configurer la simulation avec les paramètres spécifiés
    def configurer_simulation(self, lambdas, delai_retrait, capacite_buffer, mode_retrait):
        self.reseau = Reseau(lambdas, delai_retrait, capacite_buffer, mode_retrait, app = self)
        self.reseau.app = self
        
        for source in self.reseau.sources:
            source.app = self
            source.creer_buffer_canvas()
        
        self.canvas_buffer.config(width=200, height=500)
        self.actualiser_affichage()
        self.reseau.lancer_simulation()
        self.reseau.demarrer_retraits()
        self.reseau.retrait_periodique_paquet()

    # Méthode pour actualiser l'affichage des paquets dans le buffer et le lien
    def actualiser_affichage(self):
        
        self.canvas_buffer.delete("all")
        largeur_max = self.canvas_buffer.winfo_width()
        x_position = 10  
        y_position = 5  
        hauteur_paquet = 30  
        espace_horizontal = 10  
        espace_vertical = 10  

        for paquet in self.reseau.buffer_principal.file_attente:
            largeur_paquet = paquet.taille * 10
            if x_position + largeur_paquet + espace_horizontal > largeur_max:
                x_position = 10
                y_position += hauteur_paquet + espace_vertical

            x1 = x_position + largeur_paquet
            y1 = y_position + hauteur_paquet
            self.canvas_buffer.create_rectangle(x_position, y_position, x1, y1, fill=paquet.couleur)
            self.canvas_buffer.create_text((x_position + x1) / 2, (y_position + y1) / 2, text=str(paquet.paquet_id))
            x_position += largeur_paquet + espace_horizontal

        self.canvas_buffer.config(scrollregion=self.canvas_buffer.bbox("all"))

        for source in self.reseau.sources:
            source.buffer_canvas.delete("all")
            decalage_y = 40

            for paquet in source.buffer.file_attente:
                largeur_paquet = paquet.taille * 10
                if decalage_y + hauteur_paquet + 5 > source.buffer_canvas.winfo_height():
                    source.buffer_canvas.config(height=decalage_y + hauteur_paquet + 5)

                x0 = 10
                y0 = decalage_y
                x1 = 10 + largeur_paquet
                y1 = decalage_y + 30
                source.buffer_canvas.create_rectangle(x0, y0, x1, y1, fill=paquet.couleur)
                source.buffer_canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(paquet.paquet_id))
                decalage_y += hauteur_paquet + 5

            source.buffer_canvas.config(scrollregion=source.buffer_canvas.bbox("all"))
            source.calculer_taux_perdu()
            self.reseau.buffer_principal.taux_perdu_buffer_principal()

# Lancement du code en appelant la class Application qui va lancer la simulation
if __name__ == "__main__":
    app = Application()
    app.mainloop()