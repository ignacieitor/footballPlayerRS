# Librerías
import re
import sys
import os

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pycountry import countries
from unidecode import unidecode

# Mapeo de los nombres que vienen de la pagina
# al  ISO-3166-1 ALPHA-3 (con la excepcion de Reino Unido)
country_map = {
    "Bosnia-Herzegovina": "BIH",
    "Korea, South": "KOR",
    "Korea, North": "PRK",
    "DR Congo": "COD",
    "St. Kitts & Nevis": "KNA",
    "Cape Verde": "CPV",
    "Neukaledonien": "NCL",
    "Guadeloupe": "GLP",
    "Curacao": "CUW",
    "Kosovo": "XXK",
    "Niger": "NER",

    "England": "ENG",
    "Wales": "WAL",
    "Northern Ireland": "NIR",
    "Scotland": "SCO",
}

# Eliminar espacios por delante/detras
def formatPlayerName(playerIn):
    playerOut = playerIn.strip()
    return playerOut

# Formatea la posicion a unas siglas
def formatPos(posIn):
    switcher = {
        # Portero
        "Goalkeeper": "GK",
        # Defensa central
        "Centre-Back": "DF",
        "CB": "DF",
        "Defender": "DF",
        # Lateral izquierdo
        "Left-Back": "DF",
        "LB": "DF",
        # Lateral derecho
        "Right-Back": "DF",
        "RB": "DF",
        # Mediocentro defensivo
        "Defensive Midfield": "MF",
        "DM": "MF",
        # Centrocampista
        "Central Midfield": "MF",
        "CM": "MF",
        "midfield": "MF",
        # Interior izquierdo
        "Left Midfield": "MF",
        "LM": "MF",
        # Interior derecho
        "Right Midfield": "MF",
        "RM": "MF",
        # Mediocentro ofensivo
        "Attacking Midfield": "MF",
        "AM": "MF",
        # Extremo izquierdo
        "Left Winger": "FW",
        "LW": "FW",
        # Extremo derecho
        "Right Winger": "FW",
        "RW": "FW",
        # Mediapunta
        "Second Striker": "FW",
        "SS": "FW",
        # Delantero centro
        "attack": "FW",
        "Centre-Forward": "FW",
        "CF": "FW",
    }
    posOut = switcher.get(posIn, posIn)
    return posOut

# Formatea las nacionalidades de texto a ISO-3166-1 ALPHA-3
def formatNation(nationIn):
    # return countries.get(name=country_map.get(nationIn, nationIn)).alpha_3
    try:
        if nationIn in country_map:
            nationOut = country_map.get(nationIn, nationIn)
        else:
            c = countries.search_fuzzy(nationIn)
            nationOut = c[0].alpha_3
    except:
        nationOut = nationIn
    return nationOut

# Recoge la edad que venga entre parentesis (yy)
# Si contiene mas de dos caracteres, quedarnos con los dos ultimos (solo util para jugadores fallecidos)
def formatAge(ageIn):
    try:
        result = re.search('\((.*)\)', ageIn)
        ageOut = result.group(1)
        if len(ageOut) > 2:
            ageOut = ageOut[1:]
    except:
        ageOut = "NA"

    return ageOut

# Recoge la edad que venga entre parentesis (yy)
# Si contiene mas de dos caracteres, quedarnos con los dos ultimos (solo util para jugadores fallecidos)
def formatBorn_Age(born_Age):
    bornOut = "NA"
    ageOut = "NA"

    # Primero tenemos que separar dia y mes de nacimiento de año de nacimiento, edad, etc.
    aux_array = born_Age.split(", ")
    # Si no viene fecha de nacimiento
    if len(aux_array) == 1:
        aux = aux_array[0].split(" ")
    else:
        aux = aux_array[1].split(" ")

    if len(aux) > 1:
        # El primer valor sera el año de nacimento
        try:
            # Intentar convertir a entero para verificar que contiene algo
            bornOut = int(aux[0])
        except:
            # Si esta vacio o no es un numero, devolver NA
            bornOut = "NA"

        # El segundo valor sera la edad
        try:
            result = re.search('\((.*)\)', aux[1])
            ageOut = result.group(1)
            if len(ageOut) > 2:
                ageOut = ageOut[1:]
            ageOut = int(ageOut)
        except:
            ageOut = "NA"

    return str(bornOut), str(ageOut)

def formatLastClub(lastClubInfo):
    lastClub = "False"
    # Si el texto que aparece en el jugador indica que pudo jugar en dos equipos y es el ultimo donde esta
    # Si  "Joined...."  o  "Returned after loaned" --> true
    if lastClubInfo.startswith("Joined as a winter arrival from") or lastClubInfo.startswith("Returned after loan"):
        lastClub = "True"
    return lastClub

def formatValue(valueIn):
    valueOut = "NA"

    if valueIn != "":
        # Si 'm' de millones, multiplicar por 1 millon
        if valueIn[-1] == 'm':
            valueOut = str(int(float(valueIn[:-1]) * 1000000))
        # Si 'Th' de miles (thousand), multiplicar por mil
        elif valueIn[-3:] == 'Th.':
            # Multiplicar por 1000
            valueOut = str(int(float(valueIn[:-3]) * 1000))

    return valueOut

# Devuelve un listado completo (sin repetidos) de los
# equipos obtenidos de una temporada
def getTeamDataList(data):
    # Coger la columna equipo
    df = data[["Squad"]].drop_duplicates()

    return df

def canAddTransfer(data, squadIn, player, nation, position, squadOut):

    # Si se tienen datos del equipo que ficha
    if len(data.loc[data['Squad'] == squadIn]) > 0:
        # Si se encontro el jugador en el equipo del que venia
        df = data.loc[(data['Player'].apply(unidecode) == unidecode(player)) &
                      (data['Nation'] == nation) &
                      (data['Squad'] == squadOut)]
        if len(df) == 1:
            return True

        # Si se tienen datos del jugador fichado en un equipo que no sea por el que fiche
        # (esto pasa si el jugador fichado estaba cedido el año antes en ese equipo que ficha)
        df = data.loc[(data['Player'].apply(unidecode) == unidecode(player)) &
                 (data['Nation'] == nation) &
                 (data['Squad'] != squadIn)]
        # df = data.loc[(data['Squad'] == squadOut) &
        #               (data['Player'].apply(unidecode) == unidecode(player))]
        if len(df) == 1:
            return True

    return False

def main():
    # Si el numero de argumentos es correcto (webDriver, link traspasos de una liga en una temporada,
    # temporada, path datos temporada, ficheroSalida)
    if len(sys.argv)>5:
        webDriverExePath, leagueTransfersSeasonLink, season, dataDir, resultFilePath = \
            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]

        # webDriverExePath = 'C:\\Users\\Ignacieitor\\Desktop\\chromedriver_win32\\chromedriver.exe'
        options = Options()
        # Sin lanzar navegador
        # options.headless = True
        # Solo mostrar errores
        # options.add_argument("--log-level=3")
        options.add_argument("user-data-dir=C:\\Users\\Ignacieitor\\AppData\\Local\\Google\\Chrome\\User Data\\Default")
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options, executable_path=webDriverExePath)

        # Cargar datos de los valores de mercado de Transfermarkt
        iSeason = int(season)
        data = pd.read_csv(os.path.join(dataDir,
                            "fbref_transfermarkt_" + str(iSeason-1) + "_" + str(iSeason) + ".csv"), encoding='utf8')

        # Crear directorio de salida
        if not os.path.exists(os.path.dirname(resultFilePath)):
            os.makedirs(os.path.dirname(resultFilePath))

        if not os.path.exists(resultFilePath):
            with open(resultFilePath, "w", encoding='utf8') as f:
                f.write("SquadIn,Player,Nation,Pos,Value,SquadOut,Fee\n")

        # Navegar a la pagina
        # driver.get('https://www.transfermarkt.es/laliga/startseite/wettbewerb/ES1/plus/?saison_id='+season)
        print("Opening link '" + leagueTransfersSeasonLink + "'...", end='')
        # driver.get(leagueTransfersSeasonLink)
        driver.get('https://www.transfermarkt.es/laliga/startseite/wettbewerb/ES1/plus/?saison_id=2020')
        # driver.get('https://www.transfermarkt.es/laliga/transfers/wettbewerb/ES1/plus/?saison_id=2020')

        # # Hay que cambiarse de iframe antes de acceder al boton de aceptar cookies
        # WebDriverWait(driver, 10)\
        #     .until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,
        #                                                       '//iframe[@title="SP Consent Message"]')))
        # # Aceptamos las cookies por defecto
        # WebDriverWait(driver, 10)\
        #     .until(EC.element_to_be_clickable((By.XPATH,
        #                                        "//button[contains(@class,'message-component message-button no-children') and @title='ACCEPT ALL']")))\
        #     .click()
        #
        # # Volvemos a la pagina por defecto
        # driver.switch_to.default_content()
        # print("done!")

        driver.get(leagueTransfersSeasonLink)

        # Recogemos la tabla donde aparecen los equipos
        teamsTable = driver.find_elements(By.XPATH,
                                         "//div[@class='box']")
        with open(resultFilePath, "a", encoding='utf8') as f:
            for team in teamsTable:
                # Si contiene la palabra "Out " es que es un equipo con altas y bajas
                teamData = team.text
                if "Out " in teamData:
                    try:
                        squadIn = team.find_element(By.XPATH, "./div[@class='table-header']/a/img")\
                            .get_attribute("alt").strip()

                        players = team.find_element(By.XPATH, "./div[@class='responsive-table']").\
                            find_elements(By.XPATH, "./table/tbody/tr")
                        for playerRow in players:
                            try:
                                # Recoger la fila
                                # playerRow = team.find_element(By.XPATH, "./div[@class='responsive-table']/table/tbody/tr")
                                # Nombre
                                player = playerRow.find_element(By.XPATH, "./td/div/span/a[@class='spielprofil_tooltip tooltipstered']").text.strip()
                                # # Edad (No valido porque no coincide con los datos estadisticos cogidos)
                                # age = playerRow.find_element(By.XPATH, "./td[@class='zentriert alter-transfer-cell']").text.strip()
                                # Nacionalidad
                                nation = playerRow.find_element(By.XPATH, "./td/img[@class='flaggenrahmen']").get_attribute("title")
                                nation = formatNation(nation)

                                # Posicion
                                # Si no esta maximizada la pantalla, hay que usar esta clase
                                pos = playerRow.find_element(By.XPATH, "./td[@class='kurzpos-transfer-cell zentriert']").text.strip()
                                if pos == "":
                                    # Si esta maximizada la pantalla, hay que usar esta otra clase
                                    pos = playerRow.find_element(By.XPATH,
                                                                 "./td[@class='pos-transfer-cell']").text.strip()
                                pos = formatPos(pos)
                                # Valor de mercado actual
                                value = playerRow.find_element(By.XPATH, "./td[@class='rechts mw-transfer-cell']").text.strip()
                                value = formatValue(value[1:].strip())
                                # Club salida
                                squadOut = playerRow.find_element(By.XPATH, "./td[@class='no-border-rechts zentriert']/a/img").\
                                    get_attribute("alt").strip()
                                # Cantidad traspaso
                                fee = playerRow.find_element(By.XPATH, "./td[@class='rechts '] | ./td[@class='rechts bg_blau_20']").text
                                fee = formatValue(fee[1:].strip())

                                # Evaluar si se puede añadir el fichaje (si hay datos)
                                if canAddTransfer(data, squadIn, player, nation, pos, squadOut):
                                    # SquadIn, Player, Pos, Nation, Value, SquadOut, Fee
                                    playerData = squadIn + "," + player + "," + nation + "," + pos + "," + value + "," + \
                                                 squadOut + "," + fee + "\n"
                                    print(".", end='')
                                    # print(playerData)
                                    f.write(playerData)
                            except:
                                print("\nError: Error scrapping some player row!!")
                    except:
                        print("\nError: Error scrapping some team table!!")
            print("done!")
        f.close()
        print("Finished!!! Player data transfers obtained and saved to '" + resultFilePath + "'!")
        driver.quit()
    else:
        print("Command error. It must be executed with 'scraping_transfermarkt_transfers 'webDriverExePath' "
              "'link_to_the_transfer_league_season' 'season' 'fbref_tmarkt_data_path' 'resultsFilePath''")

if __name__ == "__main__":
    main()

