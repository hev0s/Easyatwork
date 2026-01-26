# --- CORRECTIF INDISPENSABLE POUR PYTHON 3.12 ---
import os
import sys

try:
    import setuptools
except ImportError:
    pass
# ------------------------------------------------

import time
import json
import urllib.parse
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Import pour lire le fichier .env
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

# --- CONFIGURATION SÉCURISÉE ---
EASY_URL = "https://app.easyatwork.com/login"
EASY_LIST_URL = "https://app.easyatwork.com/scheduling/my/list"

# Récupération des secrets depuis le fichier .env
EASY_USER = os.getenv("EASY_USER")
EASY_PASS = os.getenv("EASY_PASS")
GIRLFRIEND_EMAIL = os.getenv("GIRLFRIEND_EMAIL")

# Vérification de sécurité pour ne pas lancer le script si le .env est mal fait
if not EASY_USER or not EASY_PASS:
    print("❌ ERREUR CRITIQUE : Identifiants introuvables.")
    print("👉 Assure-toi d'avoir créé un fichier '.env' avec EASY_USER et EASY_PASS dedans.")
    sys.exit()

# Fichier historique
HISTORY_FILE = "historique_shifts.json"


def save_history(history_set):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(history_set), f)


def load_and_clean_history():
    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            history_set = set(data)
    except:
        return set()

    now_str = datetime.now().strftime("%Y%m%dT%H%M%S")
    cleaned_set = set()
    modified = False

    for uid in history_set:
        try:
            parts = uid.split('_')
            end_iso = parts[1]
            if end_iso > now_str:
                cleaned_set.add(uid)
            else:
                modified = True
        except:
            modified = True

    if modified:
        save_history(cleaned_set)
        print(f"🧹 Historique nettoyé : dates passées supprimées.")

    return cleaned_set


def convert_to_iso(date_text, time_text):
    months = {
        "janv.": "01", "févr.": "02", "mars": "03", "avr.": "04",
        "mai": "05", "juin": "06", "juil.": "07", "août": "08",
        "sept.": "09", "oct.": "10", "nov.": "11", "déc.": "12",
        "janvier": "01", "février": "02", "mars": "03", "avril": "04",
        "mai": "05", "juin": "06", "juillet": "07", "aout": "08", "août": "08",
        "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12"
    }

    try:
        parts = date_text.strip().split(' ')
        day = parts[0].zfill(2)
        month_str = parts[1].lower()
        year = parts[2]
        month = months.get(month_str, "01")
        clean_time = time_text.replace(':', '') + "00"
        return f"{year}{month}{day}T{clean_time}"
    except Exception:
        return None


def get_stealth_driver():
    print("🚀 Lancement du navigateur...")
    current_folder = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(current_folder, "chrome_profile")

    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    options = uc.ChromeOptions()
    driver = uc.Chrome(
        options=options,
        user_data_dir=profile_path,
        use_subprocess=True
    )
    driver.maximize_window()
    return driver


def scrape_shifts(driver):
    shifts = []
    print(f"--- 1. Connexion ({EASY_USER}) ---")
    driver.get(EASY_URL)
    time.sleep(3)

    try:
        popup_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Ok')]")
        if popup_btns:
            popup_btns[0].click()
            time.sleep(1)
    except:
        pass

    try:
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
        if len(email_inputs) == 0:
            print("Déjà connecté (Session active) !")
        else:
            print("Remplissage des identifiants...")
            email_field = email_inputs[0]
            driver.execute_script("arguments[0].value = arguments[1];", email_field, EASY_USER)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", email_field)

            pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            driver.execute_script("arguments[0].value = arguments[1];", pass_field, EASY_PASS)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", pass_field)

            time.sleep(0.5)
            pass_field.send_keys(Keys.RETURN)
            time.sleep(6)
    except Exception as e:
        print(f"Info Login: {e}")

    print("Navigation vers le planning...")
    driver.get(EASY_LIST_URL)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "tr")))
        time.sleep(3)
        rows = driver.find_elements(By.TAG_NAME, "tr")
        print(f"Lignes trouvées : {len(rows)}")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 7:
                date_txt = cells[4].get_attribute("textContent").strip()
                start_txt = cells[5].get_attribute("textContent").strip()
                end_txt = cells[6].get_attribute("textContent").strip()

                if "202" in date_txt and ":" in start_txt:
                    iso_start = convert_to_iso(date_txt, start_txt)
                    iso_end = convert_to_iso(date_txt, end_txt)
                    if iso_start and iso_end:
                        shifts.append({
                            "title": "Travail McDonald's",
                            "start": iso_start,
                            "end": iso_end,
                            "raw": f"{date_txt}"
                        })
                        print(f"✅ Trouvé : {date_txt}")
    except Exception as e:
        print(f"Erreur lecture tableau : {e}")

    return shifts


def add_to_google_calendar(driver, shifts):
    history = load_and_clean_history()

    new_shifts = []
    for s in shifts:
        unique_id = f"{s['start']}_{s['end']}_{s['title']}"
        if unique_id in history:
            print(f"⚠️ Déjà traité (ignoré) : {s['raw']}")
        else:
            new_shifts.append(s)

    if not new_shifts:
        print("\n🎉 Tout est déjà à jour ! Aucun nouvel horaire à ajouter.")
        return

    print(f"\n--- 2. Ajout Google Agenda ({len(new_shifts)} nouveaux) ---")
    driver.get("https://calendar.google.com/")
    time.sleep(3)

    if "signin" in driver.current_url or "ServiceLogin" in driver.current_url:
        print("\n⚠️  CONNEXION REQUISE À GOOGLE")
        while "calendar.google.com" not in driver.current_url:
            time.sleep(2)
        time.sleep(3)

    for shift in new_shifts:
        dates = f"{shift['start']}/{shift['end']}"
        text = urllib.parse.quote(shift['title'])
        location = urllib.parse.quote("McDonald's Cheseaux")

        base_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text}&dates={dates}&location={location}"

        # On utilise ici la variable récupérée du .env
        if GIRLFRIEND_EMAIL and "@" in GIRLFRIEND_EMAIL:
            base_link += f"&add={GIRLFRIEND_EMAIL}"

        driver.get(base_link)

        try:
            WebDriverWait(driver, 15).until(EC.title_contains("Google"))
            time.sleep(2)

            ActionChains(driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
            time.sleep(1)

            try:
                send_btn = driver.find_elements(By.XPATH,
                                                "//span[contains(text(), 'Envoyer')] | //span[contains(text(), 'Send')]")
                if len(send_btn) > 0:
                    send_btn[-1].click()
                    time.sleep(1)
            except:
                pass

            print(f"📅 Ajouté : {shift['raw']}")

            unique_id = f"{shift['start']}_{shift['end']}_{shift['title']}"
            history.add(unique_id)
            save_history(history)

            time.sleep(1.5)

        except Exception as e:
            print(f"❌ Erreur sur {shift['raw']} : {e}")


def main():
    driver = None
    try:
        driver = get_stealth_driver()
        shifts = scrape_shifts(driver)
        if shifts:
            add_to_google_calendar(driver, shifts)
        else:
            print("Aucun horaire trouvé.")
    finally:
        if driver:
            print("Fermeture dans 5 secondes...")
            time.sleep(5)
            try:
                driver.quit()
            except OSError:
                pass


if __name__ == "__main__":
    main()