import os

import matplotlib

from data import update
from tui import menu


if __name__ == "__main__":
    matplotlib.use('QT4Agg')
    # os.chdir("C:\\Users\\Chris\\PycharmProjects\\fmz")

    updaters = list()
    updaters.append(update.HuntingFields())
    updaters.append(update.Convoys())
    updaters.append(update.ReportSender())

    for uptater in updaters:
        uptater.start()

    menu.main_menu(updaters)

    for uptater in updaters:
        uptater.stop()

    for uptater in updaters:
        print("Waiting for \"{}\" to stop".format(uptater))
        uptater.join()

    print("Program stopped successfully")

    # TODO Idées supplémentaires :
    # - Afficher le pourcentage du temps pendant lequel un membre a une cible à flooder à portée
    # - Ajouter barres d'erreurs dans graphiques
    # - Pouvoir ajouter manuellement un convoi pour gérer la fin des demandes (auto convoi de la quantité restante)
    # - améliorer la modification et le filtre des données
    # - spellcheck pour les pseudos, et les paramètres de filtre des données
    # Détection des demandes dans pickle convoys et afficher l'historique des demandes avec la date, à voir
    # activer automatiquement les demandes, à voir

    # Si un jour je débloque les formulaires, afficher la date de dernière mise à jour dans les panels
    # + calculer la consommation et la satisfaction des besoins: Architecture, Couveuse, Laboratoire, Solarium, et
    # "Consommation par jour"
    # Rajouter de la mise en forme conditionnelle dans les tableaux

    # À voir
    # Rendre le code open source avec github mais ne pas oublier de cacher les identifiants dans un fichier perso
