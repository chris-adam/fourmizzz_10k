from datetime import datetime, timedelta
from time import sleep

import matplotlib.ticker as mtick
import PIL as pil
import numpy as np
import pandas as pd
import weasyprint as wsp
from selenium.common.exceptions import TimeoutException, InvalidCookieDomainException

from data.web import build_new_row, get_new_convoys, reconnect
from general import log


def update_fourm_pickle(name="fourm", save=True):
    name = "files/"+name
    new_row = build_new_row("Fourm")

    try:
        archive = pd.read_pickle(name)
    except FileNotFoundError:
        archive = new_row
    else:
        archive = pd.concat([archive, new_row], axis=0, ignore_index=True)

    if save:
        archive.to_pickle(name)
        log("Pickle", "Fourm", "Updated")


def update_tech_pickle(name="tech", save=True):
    name = "files/"+name
    new_row = build_new_row("Tech")

    try:
        archive = pd.read_pickle(name)
    except FileNotFoundError:
        archive = new_row
    else:
        archive = pd.concat([archive, new_row], axis=0, ignore_index=True)

    if save:
        archive.to_pickle(name)
        log("Pickle", "Tech", "Updated")


def update_hf_pickle(name="hunting_fields", save=True):
    name = "files/"+name
    archive = pd.read_pickle(name)

    new_row = build_new_row()
    archive = pd.concat([archive, new_row], axis=0, ignore_index=True)

    if save and not archive.iloc[-1, 1:].equals(archive.iloc[-2, 1:]):
        archive.to_pickle(name)
        log("Pickle", "Hunting fields", "Updated")


def get_hf(days=7):
    lower_bound_date = datetime.today() - timedelta(days=days)
    hf = pd.read_pickle("files/hunting_fields")
    hf = hf.loc[hf["Date"] > lower_bound_date, :]
    hf["Delta"] = np.NaN
    for index in hf.index[:-1]:
        hf.at[index, "Delta"] = (hf.at[index+1, "Date"] - hf.at[index, "Date"]).total_seconds()/86400
    last_delta = (pd.Timestamp.now() - hf.at[hf.index[-1], "Date"]).total_seconds()
    hf.at[hf.index[-1], "Delta"] = (last_delta-last_delta % 60)/86400

    return hf


def update_convoys(new_convoys=None):
    if new_convoys is None:
        disconnected = True
        new_convoys = None
        while disconnected:
            try:
                new_convoys = get_new_convoys()
            except TimeoutException:
                log("Web", "Convoys connection failed", "New try in 60 seconds")
                reconnect()
                sleep(60)
            except InvalidCookieDomainException:
                log("Web", "No internet for convoys", "New try in 60 seconds")
                sleep(60)
            else:
                disconnected = False

    old_convoys = pd.read_pickle("files/convoys")
    old_convoys = old_convoys.append(new_convoys).reset_index().drop("index", axis=1)
    old_convoys["Date"] = pd.to_datetime(old_convoys["Date"], format='%Y-%m-%d %H:%M:%S')
    old_convoys.drop_duplicates(inplace=True)
    old_convoys.sort_values(by="Date", inplace=True)
    old_convoys.to_pickle("files/convoys")
    log("Pickle", "Convoys", "Updated")


def received_convoys_summary(days=7):
    """Make a df with the quantity received by player during the considered period of time"""
    convoys = pd.read_pickle("files/convoys")

    requests = pd.DataFrame(columns=["Joueur", "Quantite reçue"])
    lower_bound_date = datetime.today() - timedelta(days=days)
    convoys = convoys.loc[convoys["Date"] > lower_bound_date, :]
    for recipient in convoys["Destinataire"].unique():
        quantity = convoys.loc[convoys["Destinataire"] == recipient, "Quantite"].sum()
        next_request_row = pd.DataFrame({"Joueur": recipient, "Quantite reçue": [quantity]})
        requests = requests.append(next_request_row, ignore_index=True)
    requests["Quantite reçue"] = requests["Quantite reçue"].map(mtick.EngFormatter(places=2))

    return requests


def save_df(df, file_name, new_width=750):
    """Save the dataframe in a png file"""
    def trim(source_filepath, target_filepath=None, background=None):
        if not target_filepath:
            target_filepath = source_filepath
        img = pil.Image.open(source_filepath)
        if background is None:
            background = img.getpixel((0, 0))
        border = pil.Image.new(img.mode, img.size, background)
        diff = pil.ImageChops.difference(img, border)
        bbox = diff.getbbox()
        img = img.crop(bbox) if bbox else img
        img.save(target_filepath)

    if not file_name.endswith(".png") and not file_name.endswith(".jpg"):
        file_name += ".png"
    css = wsp.CSS(string='''
    @page { size: 2048px 2048px; padding: 0px; margin: 0px; background-color: white; }
    table, td, tr, th { border: 1px solid black; }
    td, th { padding: 4px 8px; }
    ''')
    html = wsp.HTML(string=df.to_html())
    html.write_png(file_name, stylesheets=[css])
    trim(file_name)

    image = pil.Image.open(file_name)
    width, height = image.size
    new_image = image.resize((new_width, int(height * (new_width/width))))
    new_image.save(file_name)

    return file_name
