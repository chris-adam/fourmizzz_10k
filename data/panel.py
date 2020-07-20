import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from data.data import *
from general import df_selector


class FloodPanel(object):
    def __init__(self, save=False, days=7):
        # Import hunting fields and ajust time
        hf = get_hf(days=days)

        # Update mean hunting fields for each player
        self.panel = pd.read_pickle("files/hfc").drop("Étable à pucerons", axis=1)
        self.panel["Moyenne de tdc"] = 0
        self.panel["Nbr floods lancés"] = 0
        self.panel["Vol. floods lancés"] = 0.0
        self.panel["Nbr floods reçus"] = 0
        self.panel["Vol. floods reçus"] = 0.0

        for index in self.panel.index:
            self.panel.at[index, "Moyenne de tdc"] = int(round((hf[self.panel.at[index, "Joueur"]] * hf["Delta"]).sum()
                                                         / hf["Delta"].sum()))
            for hf_i1, hf_i2 in zip(hf.index[:-1], hf.index[1:]):
                if hf.at[hf_i1, self.panel.loc[index, "Joueur"]] < hf.at[hf_i2, self.panel.loc[index, "Joueur"]]:
                    self.panel.at[index, "Nbr floods lancés"] += 1
                    self.panel.at[index, "Vol. floods lancés"] += (hf.at[hf_i2, self.panel.loc[index, "Joueur"]]
                                                                   / hf.at[hf_i1, self.panel.loc[index, "Joueur"]] - 1)
                elif hf.at[hf_i1, self.panel.loc[index, "Joueur"]] > hf.at[hf_i2, self.panel.loc[index, "Joueur"]]:
                    self.panel.at[index, "Nbr floods reçus"] += 1
                    self.panel.at[index, "Vol. floods reçus"] += abs(hf.at[hf_i2, self.panel.loc[index, "Joueur"]]
                                                                     / hf.at[hf_i1, self.panel.loc[index, "Joueur"]]-1)

        # Footer
        self.panel = self.panel.append(pd.Series(), ignore_index=True)
        col_to_sum = ["Moyenne de tdc", "Nbr floods lancés", "Vol. floods lancés",
                      "Nbr floods reçus", "Vol. floods reçus"]
        for col in col_to_sum:
            self.panel.at[self.panel.index[-1], col] = self.panel[col].sum()
        self.panel.at[self.panel.index[-1], "Joueur"] = "TOTAL"
        self.panel = self.panel.replace(np.NaN, "")

        if save:
            self.save()

    def graph_repartition(self, save, show, file_name="graph_floods1.png"):
        file_name = "files/pics/" + file_name
        if not (file_name.endswith(".png") or file_name.endswith(".jpg")):
            file_name += ".png"

        # create plot
        ax = (self.panel.set_index("Joueur").loc[self.panel.set_index("Joueur").index[:-1],
                                                 "Moyenne de tdc"]) \
            .plot(kind="bar", title="Répartition du tdc", logy=True)
        ax.set_ylabel("Moyenne de tdc")

        # save plot
        if save:
            plt.tight_layout()
            ax.get_figure().savefig(file_name)
        if show:
            plt.show()

    def graph_floods(self, save, show, file_name="graph_floods2.png"):
        file_name = "files/pics/" + file_name
        if not (file_name.endswith(".png") or file_name.endswith(".jpg")):
            file_name += ".png"

        # create plot
        plt.clf()
        plt.close()
        ax = self.panel.iloc[:-1, :].plot(kind="bar", x="Joueur", y=["Nbr floods lancés", "Nbr floods reçus"],
                                          title="Activité de floods")

        # save plot
        if save:
            plt.tight_layout()
            ax.get_figure().savefig(file_name)
        if show:
            plt.show()

    def __format_panel(self):
        formatted_panel = self.panel.copy()
        formatted_panel["Moyenne de tdc"] = self.panel["Moyenne de tdc"].map(round).map('{:,}'.format)
        formatted_panel["Nbr floods lancés"] = self.panel["Nbr floods lancés"].map(round).map('{:,}'.format)
        formatted_panel["Vol. floods lancés"] = self.panel["Vol. floods lancés"].map('{0:.2%}'.format)
        formatted_panel["Nbr floods reçus"] = self.panel["Nbr floods reçus"].map(round).map('{:,}'.format)
        formatted_panel["Vol. floods reçus"] = self.panel["Vol. floods reçus"].map('{0:.2%}'.format)
        return formatted_panel

    def save(self, file_name="flood_panel.png"):
        file_name = "files/pics/" + file_name
        save_df(self.__format_panel(), file_name)

    def __str__(self):
        return self.__format_panel().to_string()


class ConvoyPanel(object):
    def __init__(self, save=False, days=7):
        hf = get_hf(days=days)
        convoys = df_selector(pd.read_pickle("files/convoys"), lower_bound_date=datetime.now()-timedelta(days=days))

        self.panel = pd.read_pickle("files/hfc").drop("Y", axis=1)
        self.panel["Moyenne de tdc"] = 0
        for index in self.panel.index:
            self.panel.at[index, "Moyenne de tdc"] = int(round((hf[self.panel.at[index, "Joueur"]] * hf["Delta"]).sum()
                                                         / hf["Delta"].sum()))
        self.panel["Pillage colo"] = 0
        self.panel["Gain colo"] = 0
        self.panel["Production"] = (self.panel["Moyenne de tdc"]*48*hf["Delta"].sum()).astype(np.int64)

        colos = pd.read_pickle("files/colos")
        for index in colos.index:
            loot_percent = 0.2 + float(self.panel.set_index("Joueur")
                                       .at[colos.at[index, "Colonisateurs"], "Étable à pucerons"])/100

            start = colos.at[index, "Début"]
            end = colos.at[index, "Fin"]
            if pd.isnull(end):
                end = datetime.now()
            time_span = (start <= hf["Date"]) & (hf["Date"] <= end)
            if not time_span.any():
                continue
            prod = int(round((hf.loc[time_span, colos.at[index, "Colonisés"]]
                              * hf.loc[time_span, "Delta"]).sum()
                             / hf.loc[time_span, "Delta"].sum()))
            prod *= 48 * hf.loc[time_span, "Delta"].sum()
            looted = int(prod*loot_percent)

            self.panel.loc[self.panel["Joueur"] == colos.at[index, "Colonisateurs"], "Gain colo"] += looted
            self.panel.loc[self.panel["Joueur"] == colos.at[index, "Colonisés"], "Pillage colo"] -= looted

        self.panel["Production"] += self.panel["Gain colo"] + self.panel["Pillage colo"]

        for index in self.panel.index:
            self.panel.at[index, "Nbr convois"] = len(convoys.loc[convoys["Livreur"] == self.panel.at[index, "Joueur"],
                                                                  "Livreur"])
            self.panel.at[index, "Volume convois"] = convoys.loc[convoys["Livreur"] == self.panel.at[index, "Joueur"],
                                                                 "Quantite"].sum()

        self.panel["Prod restante"] = self.panel["Production"] - self.panel["Volume convois"]
        if days == 7:
            days_since_beginning = (datetime.now() - datetime(2020, 5, 11, 10, 37)).days
            self.panel["Prod restante cumulée"] = ConvoyPanel(days=days_since_beginning).panel["Prod restante"]
        self.panel["Proportion livrée"] = self.panel["Volume convois"] / self.panel["Production"]
        self.panel["Proportion livrée"] = self.panel["Proportion livrée"].replace(np.NaN, 0)

        # Footer
        self.panel = self.panel.append(pd.Series(), ignore_index=True)
        col_to_sum = ["Moyenne de tdc", "Pillage colo", "Gain colo", "Production", "Nbr convois",
                      "Volume convois", "Prod restante"]
        if "Prod restante cumulée" in self.panel.columns:
            col_to_sum.append("Prod restante cumulée")
        for col in col_to_sum:
            self.panel.at[self.panel.index[-1], col] = self.panel[col].sum()
        self.panel.at[self.panel.index[-1], "Proportion livrée"] \
            = (self.panel.at[self.panel.index[-1], "Volume convois"]
               / self.panel.at[self.panel.index[-1], "Production"])
        self.panel.at[self.panel.index[-1], "Joueur"] = "TOTAL"

        self.panel = self.panel.drop("Étable à pucerons", axis=1).replace(np.NaN, "")

        if save:
            self.save()

    def graph_proportion(self, save, show, file_name="graph_convoys1.png"):
        """Save the first type of graph (proportion convoyed), needs the 'panneau convois" as input dataframe"""
        file_name = "files/pics/" + file_name
        if not file_name.endswith(".png") and not file_name.endswith(".jpg"):
            file_name += ".png"

        # create plot
        plt.clf()
        plt.close()
        ax = self.panel.set_index("Joueur")["Proportion livrée"].multiply(100)\
            .plot(kind="bar", ylim=(0, 100), title="Proportion de la production livrée")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())

        # save plot
        if save:
            plt.tight_layout()
            ax.get_figure().savefig(file_name)
        if show:
            plt.show()

    def graph_quantity(self, save, show, file_name="graph_convoys2.png"):
        """Save the second type of graph (quantity produced and convoyed),
        needs the 'panneau convois" as input dataframe"""
        file_name = "files/pics/" + file_name
        if not file_name.endswith(".png") and not file_name.endswith(".jpg"):
            file_name += ".png"

        # create plot
        plt.clf()
        plt.close()
        ax = (self.panel.set_index("Joueur").loc[self.panel.set_index("Joueur").index[:-1],
                                                 ["Production", "Volume convois"]]/10**12) \
            .plot(kind="bar", title="Production et convois")
        ax.set_ylabel("Volume de ressources (T)")

        # save plot
        if save:
            plt.tight_layout()
            ax.get_figure().savefig(file_name)
        if show:
            plt.show()

    def __format_panel(self):
        formatted_panel = self.panel.copy()
        formatted_panel["Moyenne de tdc"] = self.panel["Moyenne de tdc"].map(round).map('{:,}'.format)
        formatted_panel["Nbr convois"] = self.panel["Nbr convois"].map(round).map('{:,}'.format)
        formatted_panel["Pillage colo"] = self.panel["Pillage colo"].map(mtick.EngFormatter(places=2))
        formatted_panel["Gain colo"] = self.panel["Gain colo"].map(mtick.EngFormatter(places=2))
        formatted_panel["Production"] = self.panel["Production"].map(mtick.EngFormatter(places=2))
        formatted_panel["Volume convois"] = self.panel["Volume convois"].map(mtick.EngFormatter(places=2))
        formatted_panel["Prod restante"] = self.panel["Prod restante"].map(mtick.EngFormatter(places=2))
        if "Prod restante cumulée" in self.panel.columns:
            formatted_panel["Prod restante cumulée"] \
                = self.panel["Prod restante cumulée"].map(mtick.EngFormatter(places=2))
        formatted_panel["Proportion livrée"] = self.panel["Proportion livrée"].map('{0:.2%}'.format)
        return formatted_panel

    def save(self, file_name="convoy_panel.png"):
        file_name = "files/pics/" + file_name
        save_df(self.__format_panel(), file_name)

    def __str__(self):
        return self.__format_panel().to_string()
