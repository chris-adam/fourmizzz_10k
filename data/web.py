import os
import re
from datetime import datetime
from datetime import timedelta
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup
from engineering_notation import EngNumber
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from general import log


def get_releve(url="http://s1.fourmizzz.fr/classementAlliance.php?alliance=10000"):
    cookies = {'PHPSESSID': get_identifiants_fmz()[-1]}
    r = requests.get(url, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find(id="tabMembresAlliance")
    rows = table.find_all("tr")

    titles = ["Num", "Rank", "Pseudo", "Hf", "Tech", "Fourm"]
    releve = pd.DataFrame(columns=titles)
    for row in rows:
        lst = []
        for cell in row.find_all("td"):
            for sub_cell in cell:
                lst.append(sub_cell)
        if len(lst) == len(titles):
            releve = releve.append(pd.DataFrame({i: [a] for i, a in zip(titles, lst)}))

    return format_releve(releve)


def format_releve(releve):
    releve["Num"] = [int(i) for i in releve["Num"]]
    releve["Rank"] = [str(rank) for rank in releve["Rank"]]
    releve["Pseudo"] = [pseudo.get("href")[pseudo.get("href").find("=")+1:] for pseudo in releve["Pseudo"]]
    releve["Hf"] = [int(hf.replace(" ", "")) for hf in releve["Hf"]]
    releve["Tech"] = [int(tech) for tech in releve["Tech"]]
    releve["Fourm"] = [int(fourm) for fourm in releve["Fourm"]]
    return releve


def build_new_row(col="Hf"):
    disconnected = True
    releve = None
    while disconnected:
        try:
            releve = get_releve()
        except AttributeError:
            log("Web", "Hf connection failed", "New try in 60 seconds")
            reconnect()
            sleep(60)
        except requests.exceptions.ConnectionError:
            log("Web", "No internet for hf", "New try in 60 seconds")
            sleep(60)
        else:
            disconnected = False

    new_row = pd.DataFrame({**{"Date": [datetime.today().replace(second=0, microsecond=0)]},
                            **{pseudo: [elem] for pseudo, elem in zip(releve["Pseudo"], releve[col])}})

    return new_row


def upload_file(file_name):
    """Get a file path, upload the file and return the url"""
    # Opens browser
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        # Open upload website
        driver.get("https://www.techpowerup.org/upload")
        # Send file to website
        absolute_file_path = os.path.abspath(file_name)
        driver.find_element_by_xpath("/html/body/div/form/div[1]/input") \
            .send_keys(absolute_file_path)

        # Click to upload
        wait_for_elem(driver, "/html/body/div/form/div[4]/input", By.XPATH, 30).click()

        # Collect upload url
        url = wait_for_elem(driver, "/html/body/div/div[1]/a/img", By.XPATH, 30).get_attribute("src")
    finally:
        driver.close()
        driver.quit()

    return url


def post_forum(string, forum_id, sub_forum_name):
    """
    Post a message on the fourmizzz forum
    :param string: string to post
    :param forum_id: id of the forum to click first
    :param sub_forum_name: name of the forum in which to post
    :return: None
    """

    url = "http://s1.fourmizzz.fr/alliance.php?forum_menu"
    cookies = {'PHPSESSID': get_identifiants_fmz()[-1]}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})
        driver.get(url)

        # Click on the forum name
        wait_for_elem(driver, forum_id, By.CLASS_NAME).click()
        # Click on the subject inside the forum
        wait_for_elem(driver, sub_forum_name, By.LINK_TEXT).click()
        # Click to open answer form
        sleep(5)
        wait_for_elem(driver, "span[style='position:relative;top:-5px", By.CSS_SELECTOR).click()
        # Enter text in the form
        wait_for_elem(driver, "message", By.ID).click()
        driver.find_element_by_id("message").send_keys(string)
        # Click to send the message on the forum
        driver.find_element_by_id("repondre_focus").click()
    finally:
        driver.close()
        driver.quit()


def wait_for_elem(driver, elem, by, tps=15):
    """
    Waits for an elem to appear in a Selenium WebDriver browser
    :param driver: Selenium WebDriver
    :param elem: string of the elem to find
    :param by: find method (XPATH, ID, CLASS_NAME, ...)
    :param tps: time to wait until TimeOut
    :return: WebElement
    """
    for i in range(5):
        try:
            return WebDriverWait(driver, tps).until(ec.presence_of_element_located((by, elem)))
        except StaleElementReferenceException:
            sleep(5)


def get_new_convoys():
    """Returns a dataframe with all the convoys in 'SDC_Convois'"""

    url = "http://s1.fourmizzz.fr/alliance.php?forum_menu"
    cookies = {'PHPSESSID': get_identifiants_fmz()[-1]}
    forum_id = "forum61251.categorie_forum"

    # Opens webDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})

        driver.get(url)
        # Click on the forum name
        wait_for_elem(driver, forum_id, By.CLASS_NAME).click()
        sleep(2)

        df_convois = pd.DataFrame(columns=["Date", "Livreur", "Destinataire", "Quantite"])

        # Mark every subforum as read
        i = 2
        while i > 0:
            try:
                # if it's an "important" topic or there are no messages // or it's locked,
                if len(driver.find_elements_by_xpath("//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[1]/img")) > 0 \
                    or int(wait_for_elem(driver, "//*[@id='form_cat']/table/tbody/tr["+str(i+1)+"]/td/div/strong",
                                         By.XPATH, 2).text) == 0:
                    # or (len(driver.find_elements_by_xpath("//*[@id='form_cat']/table/tbody/tr["
                    #                                       + str(i) + "]/td[2]/img")) > 0
                    #     and wait_for_elem(driver,"//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[2]/img", By.XPATH,
                    #                       2).get_attribute('alt') == "Fermé"):
                    i += 2
                    continue

                # Click to open the sub forum
                wait_for_elem(driver, "//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[2]/a",
                              By.XPATH, 2).click()
                sleep(2)  # Wait for the page to load

                # Reset the forum
                driver.get(url)
                # Click on the forum name
                wait_for_elem(driver, forum_id, By.CLASS_NAME).click()
                sleep(1)

            # Waits if the element didn't load yet
            except (StaleElementReferenceException, IndexError):
                sleep(0.5)
            # Leave the loop if there is no more sub forum to read
            except TimeoutException:
                break
            # Go to the next sub forum
            else:
                i += 2

        # Check every sub forum for convoys
        i = 2
        while i > 0:
            try:
                # if it's an "important" topic or there are no messages // or it's locked,
                if len(driver.find_elements_by_xpath("//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[1]/img")) > 0 \
                    or int(wait_for_elem(driver, "//*[@id='form_cat']/table/tbody/tr["+str(i+1)+"]/td/div/strong",
                                         By.XPATH, 2).text) == 0:
                    # or (len(driver.find_elements_by_xpath("//*[@id='form_cat']/table/tbody/tr["
                    #                                       + str(i) + "]/td[2]/img")) > 0
                    #     and wait_for_elem(driver,"//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[2]/img", By.XPATH,
                    #                       2).get_attribute('alt') == "Fermé"):
                    i += 2
                    continue

                topic_name = wait_for_elem(driver, "//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[2]/a",
                                           By.XPATH, 2).text
                # Find the name of the requester and the amount requested
                destinataire, total_amount = topic_name.split(" - ")[1:3]
                total_amount = int(EngNumber(total_amount.replace(" ", "").replace("\u202f", "")))

                # Click to open the sub forum
                wait_for_elem(driver, "//*[@id='form_cat']/table/tbody/tr["+str(i)+"]/td[2]/a",
                              By.XPATH, 2).click()
                sleep(2)  # Wait for the page to load

                # Read every message inside the forum
                j = 2
                while j > 0:
                    try:
                        # Read the date of the convoy
                        annee = datetime.today().year
                        # if it's a new message, adapt the Xpath
                        if len(driver.find_elements_by_xpath("//*[@id='forum']/div["+str(j+1)+"]/img")) > 0:
                            date = wait_for_elem(driver, "//*[@id='forum']/div["+str(j+1)+"]/span[2]", By.XPATH, 1)\
                                .text.split()
                        else:
                            date = wait_for_elem(driver, "//*[@id='forum']/div["+str(j+1)+"]/span", By.XPATH, 1)\
                                .text.split()
                        if len(date) == 5:
                            annee = int(date[2])
                            del date[2]
                        mois = ["janv.", "févr.", "mars", "avril", "mai", "juin",
                                "juil.", "août", "sept.", "oct.", "nov.", "déc."]

                        date = datetime(annee, mois.index(date[1])+1, int(date[0]),
                                        *(int(elem) for elem in date[3].split("h")))
                        if date > datetime.today():
                            date = datetime(date.year-1, date.month, date.day, date.hour, date.minute)

                        # Read the sender
                        livreur = wait_for_elem(driver, "//*[@id='forum']/div["+str(j+1)+"]/a", By.XPATH, 2).text

                        # Read the quantity
                        quantite = wait_for_elem(driver, "//*[@id='forum']/div["+str(j+2)+"]", By.XPATH, 2).text
                        try:
                            quantite = [int(match.replace("mat", "").replace("à", "").replace("et", ""))
                                        for match in re.findall("et[0-9]+mat|et[0-9]+à", quantite.replace(" ", ""))]
                        except AttributeError:
                            log("Web", "Convoy entry incorrect",
                                "{} {} {} '"'{}'"'".format(date, livreur, destinataire, quantite))
                        else:
                            # If everything is right, append the convoy to the dataframe
                            if len(df_convois.index) > 0 \
                                    and df_convois.at[df_convois.index[-1], "Date"].minute == date.minute:
                                date += timedelta(seconds=df_convois.at[df_convois.index[-1], "Date"].second+1)
                            for s, match in enumerate(quantite):
                                df_convois = df_convois.append(pd.DataFrame({"Date": [date + timedelta(seconds=s)],
                                                                             "Livreur": [livreur],
                                                                             "Destinataire": [destinataire],
                                                                             "Quantite": [match]}),
                                                               ignore_index=True)
                                total_amount -= match

                    # Leave the loop if there is no more message to read
                    except TimeoutException:
                        # Calculate the remaining amount if needed
                        if wait_for_elem(driver, "//*[@id='forum']/div["+str(j-1)+"]/a", By.XPATH, 2).text \
                                != get_identifiants_fmz()[0] \
                                or len(quantite) > 0:
                            convoy_link = get_convoy_link(destinataire)
                            post_forum("[url="+convoy_link+"]"+destinataire+"[/url]\n\n"
                                       + "Reste: "+'{:,}'.format(total_amount).replace(",", " "),
                                       forum_id, topic_name)
                            log("Forum", "Convoy countdown update", destinataire+"'s convoys updated")

                            if total_amount <= 0:
                                send_pm(get_identifiants_fmz()[0], "[Convoys finished]",
                                        destinataire+"'s convoys finished, activation requested")
                        break
                    # Go to the next message
                    else:
                        j += 2

                # Reset the forum
                driver.get(url)
                # Click on the forum name
                wait_for_elem(driver, forum_id, By.CLASS_NAME).click()
                sleep(1)

            # Waits if the element didn't load yet
            except (StaleElementReferenceException, IndexError):
                sleep(0.5)
            # Leave the loop if there is no more sub forum to read
            except TimeoutException:
                break
            # Go to the next sub forum
            else:
                i += 2

    finally:
        driver.close()
        driver.quit()

    # Reset the indices just in case
    df_convois.reset_index(inplace=True, drop=True)

    return df_convois


def get_convoy_link(player_name):

    url = "http://s1.fourmizzz.fr/Membre.php?Pseudo=" + player_name
    cookies = {'PHPSESSID': get_identifiants_fmz()[-1]}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})
        driver.get(url)

        # get convoy link
        link = wait_for_elem(driver, "/html/body/div[4]/center/div[2]/table/tbody/tr/td[1]/a[1]", By.XPATH, 5)\
            .get_attribute('href')

    finally:
        driver.close()
        driver.quit()

    return link


def send_pm(player_name=None, subject="", text="No text"):
    if player_name is None:
        player_name = get_identifiants_fmz()[0]

    url = "http://s1.fourmizzz.fr/messagerie.php?defaut=Ecrire&destinataire=" + player_name
    cookies = {'PHPSESSID': get_identifiants_fmz()[-1]}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})
        driver.get(url)

        # write object
        wait_for_elem(driver, "/html/body/div[4]/div[1]/div[6]/div[1]/div[2]/span/input", By.XPATH, 5).click()
        wait_for_elem(driver, "/html/body/div[4]/div[1]/div[6]/div[1]/div[2]/span/input", By.XPATH, 5)\
            .send_keys(subject)

        # write main text
        wait_for_elem(driver, "/html/body/div[4]/div[1]/div[6]/div[1]/div[3]/span/textarea", By.XPATH, 5).click()
        wait_for_elem(driver, "/html/body/div[4]/div[1]/div[6]/div[1]/div[3]/span/textarea", By.XPATH, 5)\
            .send_keys(text)

        # send pm
        wait_for_elem(driver, "/html/body/div[4]/div[1]/div[6]/div[1]/div[4]/span[1]/input", By.XPATH, 50).click()
    finally:
        driver.close()
        driver.quit()

    log("Web", "Mp sent", "Mp sent to " + player_name)


def get_identifiants_fmz():
    with open("files/identifiants_fmz.txt") as file:
        identifiants = file.readlines()
        identifiants = [elem.strip() for elem in identifiants]
    return identifiants


def reconnect():
    pseudo, mdp, cook = get_identifiants_fmz()

    url = "http://s1.fourmizzz.fr"
    cookies = {'PHPSESSID': cook}

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') TODO enlever si c'est bon
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})
        driver.get(url)

        wait_for_elem(driver, "//*[@id='loginForm']/table/tbody/tr[2]/td[2]/input", By.XPATH).click()
        wait_for_elem(driver, "//*[@id='loginForm']/table/tbody/tr[2]/td[2]/input", By.XPATH).send_keys(pseudo)

        wait_for_elem(driver, "//*[@id='loginForm']/table/tbody/tr[3]/td[2]/input", By.XPATH).click()
        wait_for_elem(driver, "//*[@id='loginForm']/table/tbody/tr[3]/td[2]/input", By.XPATH).send_keys(mdp)

        wait_for_elem(driver, "//*[@id='loginForm']/input[2]", By.XPATH).click()

    except TimeoutException:
        log("Web", "Reconnection", "Reconnection failed")

    finally:
        driver.close()
        driver.quit()
