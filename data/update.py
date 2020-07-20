import pickle
from threading import Thread, RLock
from time import time

from data import panel, data
from data.web import *

lock_hf = RLock()
lock_convoys = RLock()
lock_report = RLock()


class HuntingFields(Thread):
    def __init__(self, save_pickle=True):
        Thread.__init__(self)
        self.pursue = True

        self.save_pickle = save_pickle

    def run(self):
        while self.pursue:
            with lock_hf:
                # Update pickle hunting_fields
                data.update_hf_pickle(save=self.save_pickle)
            sleep(3)

    def stop(self):
        self.pursue = False

    def stopped(self):
        return not self.pursue

    def __str__(self):
        return "Hunting field updater"


class Convoys(Thread):
    def __init__(self, update_delay_convoys=2*60*60):
        Thread.__init__(self)
        self.pursue = True
        self.update_delay_convoys = update_delay_convoys  # seconds
        self.time_convoys = time()-self.update_delay_convoys

    def run(self):
        """Code à exécuter pendant l'exécution du thread."""
        while self.pursue:
            with lock_convoys:
                if time()-self.time_convoys >= self.update_delay_convoys:
                    self.time_convoys = time()
                    data.update_convoys()
            sleep(1)

    def stop(self):
        self.pursue = False

    def stopped(self):
        return not self.pursue

    def __str__(self):
        return "Convoys updater"


class ReportSender(Thread):
    def __init__(self, delay_report=7*24*60*60):
        Thread.__init__(self)
        self.pursue = True

        self.delay_report = delay_report  # seconds
        with open("files/last_report_date", "rb") as file:
            self.time_report = pickle.Unpickler(file).load()

    def run(self):
        while self.pursue:
            with lock_report:
                if time()-self.time_report >= self.delay_report:
                    # pickle the date
                    with open("files/last_report_date", "wb") as file:
                        pickle.Pickler(file).dump(time())
                    # send report
                    self.send()

            with open("files/last_report_date", "rb") as file:
                self.time_report = pickle.Unpickler(file).load()

            sleep(1)

    def send(self):
        log("Forum", "Report", "Writing report")

        # Collect data and update
        new_convoys = get_new_convoys()
        data.update_convoys(new_convoys)
        request_history = data.received_convoys_summary()
        fourm, tech = self.get_stats_changes()

        # Draw graphs and table for floods
        flood_panel = panel.FloodPanel(save=True)
        flood_panel.graph_repartition(save=True, show=False)
        flood_panel.graph_floods(save=True, show=False)

        # Draw graphs and table for convoys
        convoy_panel = panel.ConvoyPanel(save=True)
        convoy_panel.graph_quantity(save=True, show=False)
        convoy_panel.graph_proportion(save=True, show=False)

        # Post report to forum
        post_forum("[size=4][u][b]Rapport automatique sur les 7 derniers jours[/b][/u][/size]"
                   + "\n\n\n" + "[b]Données sur les floods[/b]"
                   + "\n\n" + "[img]" + upload_file("files/pics/flood_panel.png") + "[/img]"
                   + "\n\n" + "[img]" + upload_file("files/pics/graph_floods1.png") + "[/img]"
                   + "\n\n" + "[img]" + upload_file("files/pics/graph_floods2.png") + "[/img]"
                   + "\n\n\n" + "[b]Données sur les convois[/b]"
                   + "\n\n" + "[u]Historique des convois reçus :[/u]"
                   + "\n" + request_history.to_string(index=False, header=False)
                   + "\n\n" + "[img]" + upload_file("files/pics/convoy_panel.png") + "[/img]"
                   + "\n\n" + "[img]" + upload_file("files/pics/graph_convoys1.png") + "[/img]"
                   + "\n\n" + "[img]" + upload_file("files/pics/graph_convoys2.png") + "[/img]"
                   + "\n\n\n" + "[b]Données sur les évolutions[/b]"
                   + "\n\n" + "[u]Constructions :[/u]"
                   + "\n" + "[img]" + upload_file(data.save_df(fourm, "files/pics/fourm.png",
                                                               min(700, 200+70*(len(fourm.columns)-1)))) + "[/img]"
                   + "\n\n" + "[u]Technologies :[/u]"
                   + "\n" + "[img]" + upload_file(data.save_df(tech, "files/pics/tech.png",
                                                               min(700, 200+70*(len(tech.columns)-1)))) + "[/img]",
                   forum_id="forum58795.categorie_forum",
                   sub_forum_name="Rapports automatiques")

        log("Forum", "Report", "Report sent to forum", print_log=True)

    def get_stats_changes(self):
        data.update_fourm_pickle()
        data.update_tech_pickle()
        days = self.delay_report/24/60/60
        target_date = datetime.today()-timedelta(days=days)

        fourm = pd.read_pickle("files/fourm")
        closest_date_fourm = datetime.today()
        for date in fourm.loc[fourm.index[:-1], "Date"]:
            if abs(date-target_date) < abs(closest_date_fourm-target_date):
                closest_date_fourm = date
        fourm.set_index("Date", inplace=True)
        fourm = pd.concat([pd.DataFrame(fourm.loc[closest_date_fourm, :]),
                           pd.DataFrame(fourm.iloc[-1, :])], axis=1).transpose()
        fourm = fourm.loc[:, (fourm != fourm.iloc[0]).any()].dropna(how="all", axis=1)

        tech = pd.read_pickle("files/tech")
        closest_date_tech = datetime.today()
        for date in tech.loc[tech.index[:-1], "Date"]:
            if abs(date-target_date) < abs(closest_date_tech-target_date):
                closest_date_tech = date
        tech.set_index("Date", inplace=True)
        tech = pd.concat([pd.DataFrame(tech.loc[closest_date_tech, :]),
                          pd.DataFrame(tech.iloc[-1, :])], axis=1).transpose()
        tech = tech.loc[:, (tech != tech.iloc[0]).any()].dropna(how="all", axis=1)

        return fourm, tech

    def stop(self):
        self.pursue = False

    def stopped(self):
        return not self.pursue

    def __str__(self):
        return "Report sender"
