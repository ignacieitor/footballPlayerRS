# Librerías
import re
import sys
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pycountry import countries

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
        "Centre-Back": "DFC", #"DF",
        "Defender": "DFC",
        # Lateral izquierdo
        "Left-Back": "DFL", #"DF",
        # Lateral derecho
        "Right-Back": "DFR", #"DF",
        # Mediocentro defensivo
        "Defensive Midfield": "MFD", #"MF",
        # Centrocampista
        "Central Midfield": "MF",
        "midfield": "MF",
        # Interior izquierdo
        "Left Midfield": "MFL",
        # Interior derecho
        "Right Midfield": "MFR",
        # Mediocentro ofensivo
        "Attacking Midfield": "MFO", #"MF",
        # Extremo izquierdo
        "Left Winger": "FWL", #"FW",
        # Extremo derecho
        "Right Winger": "FWR", #"FW",
        # Mediapunta
        "Second Striker": "FW",
        # Delantero centro
        "attack": "FWC", #"FW",
        "Centre-Forward": "FWC", #"FW",
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

def formatMarketValue(valueIn):
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

def main():
    # Si el numero de argumentos es correcto (webDriver, nombre liga, liga+temporada, ficheroSalida)
    if len(sys.argv)>4:
        webDriverExePath, leagueName, leagueSeasonLink, resultFilePath = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

        # webDriverExePath = 'C:\\Users\\Ignacieitor\\Desktop\\chromedriver_win32\\chromedriver.exe'
        options = Options()
        # Sin lanzar navegador
        options.headless = True
        # Solo mostrar errores
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=options, executable_path=webDriverExePath)

        # Crear directorio de salida
        if not os.path.exists(os.path.dirname(resultFilePath)):
            os.makedirs(os.path.dirname(resultFilePath))

        if not os.path.exists(resultFilePath):
            with open(resultFilePath, "w", encoding='utf8') as f:
                f.write("Comp,Squad,Number,Player,Pos,Age,Born,Nation,Value,LastClub\n")

        # Navegar a la pagina
        # driver.get('https://www.transfermarkt.es/laliga/startseite/wettbewerb/ES1/plus/?saison_id='+season)
        print("Opening link '" + leagueSeasonLink + "'...", end='')
        driver.get(leagueSeasonLink)

        # Hay que cambiarse de iframe antes de acceder al boton de aceptar cookies
        WebDriverWait(driver, 10)\
            .until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,
                                                              '//iframe[@title="SP Consent Message"]')))
        # Aceptamos las cookies por defecto
        WebDriverWait(driver, 10)\
            .until(EC.element_to_be_clickable((By.XPATH,
                                               "//button[contains(@class,'message-component message-button no-children') and @title='ACCEPT ALL']")))\
            .click()

        # Volvemos a la pagina por defecto
        driver.switch_to.default_content()
        print("done!")

        # Recogemos la tabla donde aparecen los equipos
        teamsTable = driver.find_element(By.XPATH,
                                         "//div[@id='yw1']")
        teams = teamsTable.find_elements(By.XPATH,
                                         "./table/tbody/tr/td[@class='zentriert no-border-rechts']/a[@class='vereinprofil_tooltip tooltipstered']")

        # Recogemos los links de las paginas de cada uno de los equipos de ese año
        teams_links = [team.get_attribute('href') for team in teams]
        for t_link in teams_links:
            print("Opening link '" + t_link + "'...", end='')
            # Navegamos a la pagina del equipo
            driver.get(t_link)
            # Ejemplo Huesca con jugador sin fecha nacimiento
            # driver.get("https://www.transfermarkt.com/sd-huesca/startseite/verein/5358/saison_id/2020")
            # Ejemplo Nantes con jugador fallecido
            # driver.get("https://www.transfermarkt.com/fc-nantes/startseite/verein/995/saison_id/2018")
            # Ejemplo Barcelona 17/18
            # driver.get("https://www.transfermarkt.com/fc-barcelona/startseite/verein/131/saison_id/2017")

            # Guardamos el nombre de la liga
            # comp = driver.find_element(By.XPATH, "//span[@class='hauptpunkt']").text
            # Eliminar espacios por delante/detras
            # comp = comp.strip()

            # Guardamos el nombre del equipo correspondiente
            squad = driver.find_element(By.XPATH, "//div[@class='dataName']").text
            # Eliminar espacios por delante/detras
            squad = squad.strip()
            print("done!")
            print("Obtaining " + squad + " players", end='')
            # Recoger los datos de la tabla de cada uno de los jugadores de ese equipo
            playersTable = driver.find_element(By.XPATH, "//div[@id='yw1']")
            players = playersTable.find_elements(By.XPATH,
                                                 "./table/tbody/tr[@class='odd' or @class='even']")
            with open(resultFilePath, "a", encoding='utf8') as f:
                for p in players:
                    try:
                        # Partimos los datos de cada fila
                        playerRow = p.text.strip().split('\n')
                        # player_number = p.find_element(By.XPATH, "./td/div[@class='rn_nummer']").text
                        # En algunos equipos no viene el dorsal (-) aunque realmente jugaron en el primer equipo ese año
                        if len(playerRow) > 3:
                            # Dorsal
                            number = playerRow[0]
                            # Nombre del jugador
                            # Eliminar espacios por delante/detras
                            player = formatPlayerName(playerRow[1])
                            # Demarcacion (formateada a lo obtenido en fbref)
                            pos = formatPos(playerRow[2])
                            born, age = formatBorn_Age(playerRow[3])

                            # Valor de mercado
                            value = p.find_element(By.XPATH, "./td[@class='rechts hauptlink']").text
                            value = formatMarketValue(value[1:].strip())

                            # Nacionalidad
                            nation = p.find_element(By.XPATH, "./td/img[@class='flaggenrahmen']").get_attribute("title")
                            nation = formatNation(nation)

                            # Para sacar si fue fichaje de invierno (si existe)
                            try:
                                tradeInfo = p.find_element(By.XPATH, "./td/a[@class='hide-for-small']").get_attribute("title")
                                lastClub = formatLastClub(tradeInfo)
                            except:
                                lastClub = "False"

                            # Comp, Squad, Number, Player, Pos, Age, Born, Nation, Value, LastClub
                            playerData = leagueName + "," + squad + "," + number + "," + player + "," + \
                                         pos + "," + age + "," + born + "," + nation + "," + value + "," + lastClub + "\n"
                            print(".", end='')
                            # print(playerData)
                            f.write(playerData)
                    except:
                        print("\nError: The player '" + player + "' could not be scrapped!")
                print("done!")
            f.close()
        print("Finished!!! Player data obtained and saved to '" + resultFilePath + "'!")
        driver.quit()
    else:
        print("Command error. It must be executed with 'scraping_transfermarkt 'webDriverExePath' 'league_name' 'link_to_the_league_season' 'resultsFilePath''")

if __name__ == "__main__":
    main()

