import pickle
from queue import Queue
from time import time
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd

from data import panel, data, update
from general import df_selector


def main_menu(updaters):
    main_menu_text = "\n- ~ - 10K MENU - ~ -\n" \
                     "1) Flood panel\n" \
                     "2) Convoy panel\n" \
                     "3) graph\n" \
                     "4) Data\n" \
                     "5) Modify\n" \
                     "6) Manual update\n" \
                     "7) Options\n" \
                     "8) Repair\n" \
                     "9) Exit"

    print("You can enter multiple choices to fast travel through menus.")

    choice = 1
    while choice != 9:
        try:
            print(main_menu_text)
            choices = Queue()
            choice = get_choice(choices)

            if choice == 1:
                print(panel.FloodPanel())
            elif choice == 2:
                print(panel.ConvoyPanel())
            elif choice == 3:
                graph_menu(choices)
            elif choice == 4:
                data_menu(choices)
            elif choice == 5:
                modify_menu(choices)
            elif choice == 6:
                manuel_update_menu(choices, updaters)
            elif choice == 7:
                options_menu(choices)
            elif choice == 8:
                for updater in updaters:
                    if not updater.is_alive():
                        updaters.remove(updater)
                        new_thread = type(updater)()
                        new_thread.start()
                        updaters.append(new_thread)
                        print(updater, "repaired")
                print("Finished repairing")
            elif choice == 9:
                print("Leaving...")
            else:
                raise ValueError

        except ValueError:
            print("Wrong input")


def graph_menu(choices):
    graph_menu_text = "\n-- Graph menu --\n" \
                      "1) Hunting field repartition along players\n" \
                      "2) Flood activity by player\n" \
                      "3) Proportion of resource production convoyed\n" \
                      "4) Resource production by player\n" \
                      "5) Alliance hunting field at a glance"

    print(graph_menu_text)
    choice = get_choice(choices)

    if choice == 1:
        panel.FloodPanel().graph_repartition(show=True, save=False)
    elif choice == 2:
        panel.FloodPanel().graph_floods(show=True, save=False)
    elif choice == 3:
        panel.ConvoyPanel().graph_proportion(show=True, save=False)
    elif choice == 4:
        panel.ConvoyPanel().graph_quantity(show=True, save=False)
    elif choice == 5:
        players = pd.read_pickle("files/hfc")["Joueur"]
        pd.read_pickle("files/hunting_fields").set_index("Date").loc[:, players].sum(axis=1).divide(10**9)\
            .plot(title="Évolution du tdc de l'alliance").set_ylabel("Tdc (G cm²)")
        plt.show()
    else:
        raise ValueError


def data_menu(choices):
    data_menu_text = "\n-- Data menu --\n" \
                     "1) Chain\n" \
                     "2) Colonisations\n" \
                     "3) Hunting fields\n" \
                     "4) Convoys\n" \
                     "5) Logs\n" \
                     "6) Next report date"

    print(data_menu_text)
    choice = get_choice(choices)
    with open("files/options", "rb") as file:
        options = pickle.Unpickler(file).load()

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        if choice == 1:
            print(pd.read_pickle("files/hfc").to_string(na_rep=""))
        elif choice == 2:
            print(pd.read_pickle("files/colos").to_string())
        elif choice == 3:
            print(df_selector(pd.read_pickle("files/hunting_fields"), **options["hf"], drop_dup=True).to_string())
        elif choice == 4:
            print(df_selector(pd.read_pickle("files/convoys"), **options["convoys"]).to_string(index=False))
        elif choice == 5:
            print(df_selector(pd.read_pickle("files/logs"), **options["logs"]).to_string(index=False))
        elif choice == 6:
            with open("files/last_report_date", "rb") as file:
                print((datetime.fromtimestamp(pickle.Unpickler(file).load()) + timedelta(days=7))
                      .replace(microsecond=0))
        else:
            raise ValueError


def modify_menu(choices):
    modify_menu_text = "\n-- Modification menu --\n" \
                       "1) Chain\n" \
                       "2) Colonisations\n" \
                       "3) Clear all logs"

    print(modify_menu_text)
    choice = get_choice(choices)

    if choice == 1:
        modify(choices, "files/hfc")
    elif choice == 2:
        modify_colos(choices)
    elif choice == 3:
        if input("Are you sure ? (y/n)").lower().startswith("y"):
            logs = pd.read_pickle("files/logs")
            logs.drop(logs.index).to_pickle("files/logs")
            print("Logs cleared")
        else:
            print("Operation cancelled")
    else:
        raise ValueError


def modify_colos(choices):
    modify_text = "\n-- Editing data --\n" \
                  "1) Add colo\n" \
                  "2) End colo\n" \
                  "3) Edit\n" \
                  "4) Delete"

    print(modify_text)
    choice = get_choice(choices)

    colos = pd.read_pickle("files/colos")
    print(colos)

    if choice == 1:
        colonisateur = input("Nom du colonisateur: ")
        colonie = input("Nom de la colonie: ")
        colos = colos.append(pd.DataFrame({"Début": [datetime.now().replace(microsecond=0)],
                                           "Colonisés": [colonie],
                                           "Colonisateurs": [colonisateur]}),
                             ignore_index=True)
    elif choice == 2:
        row = int(input("Select row number: "))
        colos.at[row, "Fin"] = datetime.now().replace(microsecond=0)
    elif choice == 3:
        row = int(input("Select row number: "))
        for col_name in colos.columns[2:]:
            new_value = input(col_name+" (leave empty to leave unchanged): ")
            if new_value != "":
                colos.at[row, col_name] = new_value
    elif choice == 4:
        row = int(input("Select row number: "))
        colos = colos.drop(row).reset_index(drop=True)
    else:
        raise ValueError

    print(colos)
    colos.to_pickle("files/colos")


def modify(choices, file_name):
    modify_text = "\n-- Editing data --\n" \
                  "1) Add\n" \
                  "2) Edit\n" \
                  "3) Delete"

    print(modify_text)
    choice = get_choice(choices)
    df = pd.read_pickle(file_name)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df.to_string(na_rep=""))

        if choice == 1:
            row_index = int(input("Select position where to insert: "))
            new_row = {}.fromkeys(df.columns)
            for key in new_row:
                new_row[key] = input(key+": ")
            new_row = pd.DataFrame(new_row, index=[0])
            df = pd.concat([df.iloc[:row_index], new_row, df.iloc[row_index:]]).reset_index(drop=True)
        elif choice == 2:
            row_index = int(input("Select position where to edit: "))
            new_row_index = input("Select new position: ")
            new_row_index = row_index if new_row_index == "" else int(new_row_index)

            new_row = {}.fromkeys(df.columns)
            for key in new_row:
                new_row[key] = input(key+": ")
                if new_row[key] == "":
                    new_row[key] = df.at[row_index, key]

            new_row = pd.DataFrame(new_row, index=[0])
            df = pd.concat([df.iloc[:row_index], new_row, df.iloc[row_index+1:]]).reset_index(drop=True)

            new_indices = list(df.index)
            new_indices[row_index] = "to_drop"
            new_indices.insert(new_row_index, row_index)
            new_indices.remove("to_drop")
            df = df.reindex(new_indices).reset_index(drop=True)
        elif choice == 3:
            try:
                row_index = int(input("Select row index: "))
                df = df.drop(row_index).reset_index(drop=True)
            except KeyError:
                print("KeyError: row", row_index, "could not be deleted")
        else:
            raise ValueError

    df.to_pickle(file_name)


def manuel_update_menu(choices, updaters):
    manuel_update_menu_text = "\n-- Manual update menu --\n" \
                              "1) Update hunting fields\n" \
                              "2) Update convoys\n" \
                              "3) Send report to forum"

    print(manuel_update_menu_text)
    choice = get_choice(choices)

    if choice == 1:
        data.update_hf_pickle()
    elif choice == 2:
        data.update_convoys()
    elif choice == 3:
        for updater in updaters:
            if isinstance(updater, update.ReportSender):
                updater.send()
        with open("files/last_report_date", "wb") as file:
            pickle.Pickler(file).dump(time())
    else:
        raise ValueError


def options_menu(choices):
    options_menu_text = "\n-- Options menu --\n" \
                        "1) Logs selector\n" \
                        "2) Convoys selector\n" \
                        "3) Hunting fields selector"

    print(options_menu_text)
    choice = get_choice(choices)
    with open("files/options", "rb") as file:
        options = pickle.Unpickler(file).load()

    if choice == 1:
        option = "logs"
    elif choice == 2:
        option = "convoys"
    elif choice == 3:
        option = "hf"
    else:
        raise ValueError

    # Display actual options
    print("- Actual", option, "options:")
    for k, v in options[option].items():
        print(k+":", v)

    # input new options
    print("- New", option, "options (leave empty to leave unchanged):")
    value = input("Number of last rows to display (0 to show all):")
    options[option]["nrows"] = int(value) if value != "" else options[option]["nrows"]
    value = input("lower_bound_date (YYYY-MM-DD HH:MM:SS): ")
    options[option]["lower_bound_date"] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value != "" \
        else options[option]["lower_bound_date"]
    value = input("upper_bound_date (YYYY-MM-DD HH:MM:SS): ")
    options[option]["upper_bound_date"] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value != "" \
        else options[option]["upper_bound_date"]
    value = input("Keep filter ({column: [values]}):")
    options[option]["keep"] = eval(value) if value != "" else options[option]["keep"]
    value = input("Exclude filter ({column: [values]}):")
    options[option]["exclude"] = eval(value) if value != "" else options[option]["exclude"]

    # Save options
    with open("files/options", "wb") as file:
        pickle.Pickler(file).dump(options)


def get_choice(choices):
    if choices.empty():
        for choice in list(input(">>> ")):
            choices.put(int(choice))
        next_choice = choices.get()
    else:
        next_choice = choices.get()
        print(">>>", next_choice)

    return next_choice


# TODO pas urgent
# Afficher un graphique quelconque: + autres
#   nombre de floods en fonction du temps, nbr de convois f(t), volume convois f(t),
#   en fonction du moment de la journée
# Afficher l'historique des relevés de tdc, pouvoir filtrer par joueur, par modification de tdc
# Afficher l'historique des convois, pouvoir filtrer/trier par livreur, destinataire, quantité
#   afficher des stats liées aux convois comme le nombre de convois reçus/livrés entre les dates demandées
# Historique des floods reçus/lancés par joueur
# Clear les logs (entre certains dates/certain nombre)
# Afficher texte pour MC chaine, greniers, passeurs ou chasseurs
# Afficher la date du prochain rapport
