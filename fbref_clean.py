import os
import sys
import pandas as pd

from difflib import SequenceMatcher
from functools import lru_cache
from pycountry import countries

# Mapeo de los nombres que vienen de la pagina
# al ISO-3166-1 ALPHA-3 (con la excepcion de Reino Unido)
from unidecode import unidecode

COUNTRY_MAP = {
    'ANG': 'AGO', # Angola
    'CGO': 'COG', # Republic of the Congo
    'CHA': 'TCD', # Chad
    'CRC': 'CRI', # Costa Rica
    'CTA': 'CAF', # Central African Republic
    'EQG': 'GNQ', # Equatorial Guinea
    'GPE': 'GLP', # Guadeloupe
    'KVX': 'XXK', # Kosovo
    'MTN': 'MRT', # Mauritania
    'HAI': 'HTI', # Haiti
    'HON': 'HND', # Honduras
    'KSA': 'SAU', # Saudi Arabia
    'NED': 'NLD', # Netherlands
    'NIG': 'NER', # Niger
    'NOR': 'NOR', # Norway (añadido porque si no devuelve France)
    'RSA': 'ZAF', # South Africa
    'SUI': 'CHE', # Switzerland
    'URU': 'URY', # Uruguay (añadido porque si no devuelve Burundi

    'ENG': 'ENG', # England
    'WAL': 'WAL', # Wales
    'NIR': "NIR", # Northern Ireland
    'SCO': "SCO", # Scotland
}

# Hay equipos que tienen el nombre muy distinto entre FBRef y Transfermarkt,
# por lo que es necesaria una tabla de mapeos
TEAM_MAP = {
    'Rennes': 'Stade Rennais FC',
}

def formatHeader(statFileName):
    header = ""
    if "StandardStats" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,MP,Starts,Min,Min/90,Gls,Ast,G-PK,PK,PKatt,CrdY,CrdR," \
                 "Gls/90,Ast/90,G+A/90,G-PK/90,G+A-PK/90,xG,npxG,xA,npxG+xA,xG/90,xA/90,xG+xA/90,npxG/90,npxG+xA/90"
    elif "Goalkeeping" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,MP,Starts,Min,Min/90,GA,GA/90," \
                 "SoTA,Saves,Save%,W,D,L,CS,CS%,PKA,PKGA,PKsv,PKm,PK%"
    elif "Shooting" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,Gls,Sh,SoT,SoT%,Sh/90,SoT/90," \
                 "G/Sh,G/SoT,Dist,FK,PK,PKatt,xG,npxG,npxG/Sh,G-xG,np:G-xG"
    elif "Passing" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,P_Cmp,P_Att,P_Cmp%," \
                 "P_TotDist,P_PrgDist,PS_Cmp,PS_Att,PS_Cmp%,PM_Cmp,PM_Att,PM_Cmp%,PL_Cmp," \
                 "PL_Att,PL_Cmp%,Ast,xA,A-xA,P_KP,P_1/3,P_PPA,P_CrsPA,P_Prog"
    elif "Pass_Types" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,P_Att,P_Live,P_Dead," \
                 "P_FK,P_TB,P_Press,P_Sw,P_Crs,P_CK,P_InCK,P_OutCK,P_StrCK,P_Ground,P_Low," \
                 "P_High,P_Left,P_Right,P_Head,P_TI,P_Other,P_Cmp,P_Off,P_Out,P_Int,P_Blocks"
    elif "Goal_and_Shot_Creation" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,SCA,SCA/90,PassLiveSh,PassDeadSh," \
                 "DribSh,ShSh,FldSh,DefSh,GCA,GCA/90,PassLiveG,PassDeadG,DribG,ShG,FldG,DefG"
    elif "Defensive_Actions" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,TklPl,TklW,TkDef3rd,TkMid3rd,TkAtt3rd," \
                 "TklDr,TklDrAtt,TklDr%,DrPast,PressAtt,PressSucc,Press%,PressDef3rd,PressMid3rd,PressAtt3rd," \
                 "Blocks,BlocksSh,BlocksSoT,BlocksPass,Int,Tkl+Int,Clr,ErrSh"
    elif "Possession" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,Touches,TouchesDefPen," \
                 "TouchesDef3rd,TouchesMid3rd,TouchesAtt3rd,TouchesAttPen,TouchesLive,DribSucc,DribAtt," \
                 "DribSucc%,DribPl,Megs,Carries,TotDist,PrgDist,Prog,1/3,CPA,Mis,Dis,Targ,Rec,Rec%,PR_Prog"
    elif "Miscellaneous_Stats" in statFileName:
        header = "Rk,Player,Nation,Pos,Squad,Comp,Age,Born,Min/90,CrdY,CrdR,2CrdY," \
                 "FlsCom,FlsRec,Off,Crs,Int,TklW,PKRec,PKCom,OG,Recov,AWon,ALost,AWon%"
    return header

# Convierte las posiciones
def formatPosition(posIn):
    switcher = {
        "GKDF": "GK",
        "GKMF": "GK",
        "GKFW": "GK",
        "DFFW": "DF",
        "DFMF": "DF",
        "MFDF": "MF",
        "MFFW": "MF",
        "FWDF": "FW",
        "FWMF": "FW",
    }
    posOut = switcher.get(posIn, posIn)
    return posOut

@lru_cache()
def formatNation(nationIn):
    # Puede venir con dos campos o uno (en ENG o ENG)
    try:
        nationIn = nationIn.split()[1]
    except:
        nationIn = nationIn

    try:
        if nationIn in COUNTRY_MAP:
            nationOut = COUNTRY_MAP.get(nationIn, nationIn)
        else:
            c = countries.search_fuzzy(nationIn)
            nationOut = c[0].alpha_3
    except:
        nationOut = nationIn
    return nationOut

# Convierte un array de campos a una linea separada por comas
def formatPlayerLine(playerFields):
    lineOut=""
    for f in playerFields:
        lineOut = lineOut + f + ","
    lineOut = lineOut[:-1]
    return lineOut

# Funcion para limpiar los datos por temporada de FBRef, dar un
# mejor formato y que asi cuadren mejor con los datos de Transfermarkt
def cleanFBRefStats(dataFbrPath, dataTmarktPath, season):
    fbrSeasonDir = os.path.join(dataFbrPath, season)
    df_tm = pd.read_csv(os.path.join(dataTmarktPath, "transfermarkt_"+season+".csv"), encoding='utf8', dtype=str)
    # tmarktTeamList = getTeamListFromTransfermarkt(df_tm)
    tmarktTeamData = getTeamDataFromTransfermarkt(df_tm)

    statFiles = os.listdir(fbrSeasonDir)
    print(statFiles)
    for sf in statFiles:
        filePath = os.path.join(fbrSeasonDir, sf)
        resultFilePath = os.path.join(fbrSeasonDir, "out\\fbref_" + sf)
        print("Processing file '" + filePath + "'...", end="")
        df = pd.read_csv(filePath, encoding='utf8', dtype=str)
        # Modificar columnas
        df.columns = formatHeader(sf).split(",")
        print(".", end="")
        # Formatear el campo nacionalidad (Nation)
        df["Nation"] = df.apply(lambda row: formatNation(row["Nation"]), axis=1)
        print(".", end="")
        # Formatear el campo posicion (Pos)
        df["Pos"] = df.apply(lambda row: formatPosition(row["Pos"]), axis=1)
        print(".", end="")
        # Formatear el campo liga (Comp)
        df["Comp"] = df.apply(lambda row: row["Comp"][row["Comp"].index(" ")+1:], axis=1)
        print(".", end="")
        # Formatear el campo equipo (Squad)
        df["Squad"] = df.apply(lambda row: getTFMarktTeamName(row, tmarktTeamData), axis=1)
        print(".", end="")
        # Formatear el campo nombre (Player)
        df["Player"] = df.apply(lambda row: getTFMarktPlayerName(row, df_tm), axis=1)
        print(".", end="")
        # Crear directorio de salida
        if not os.path.exists(os.path.dirname(resultFilePath)):
            os.makedirs(os.path.dirname(resultFilePath))
        # Guardar
        df.to_csv(resultFilePath, index=False, encoding='utf8')
        print("OK. Saved to '" + resultFilePath + "'")
        # Eliminar fichero origen
        # os.remove(filePath)

# Devuelve un listado completo (sin repetidos)
# de los jugadores obtenidos de una temporada de FBRef
def getTeamListFromFBRef(filePath):
    # Lista evitando repetidos
    teamList = set()
    df = pd.read_csv(filePath, encoding='utf8', dtype=str)
    # Recuperar los elementos unicos de la columna equipo
    list = df["Squad"].unique().tolist()
    for t in list:
        teamList.add(t)

    teamList = sorted(teamList)
    return teamList

# Devuelve un listado completo (sin repetidos) de los
# equipos obtenidos de una temporada en Transfermarkt
def getTeamDataFromTransfermarkt(data):
    # Coger las columnas liga, equipo
    df = data[["Comp", "Squad"]].drop_duplicates()

    return df

# Transforma el nombre de un jugador del dataset de BRRef al de TransferMarkt
# Para ello hara lo siguiente:
# 0. Buscar por club, nombre del jugador (la mayoria)
# 1. Buscar por club, nombre del jugador (sin caracteres fuera del ascii)
# 2. Buscar por club, año de nacimiento
# 2.1 Si al aplicar este filtro, hay algun jugador con gran similitud en su nombre, cogerlo y salir
# 3. Buscar por club, nacionalidad, año de nacimiento
# Si en cualquiera de los 4 escenarios saliera mas de uno, calcular la distancia de Hamming
# y quedarnos con el nombre que devuelva el valor mas parecido
# Si no se encontrara, quedarnos con el valor de FBRef
def getTFMarktPlayerName(dataPlayerFBref, dataTMarkt):
    # Por defecto, devolver el nombre que venia
    player = dataPlayerFBref["Player"].split("\\")[0]

    # 0. Buscar por club, nombre del jugador (la mayoria)
    df = dataTMarkt.loc[(dataTMarkt['Squad'] == dataPlayerFBref['Squad']) &
                        (dataTMarkt['Player'] == player)]
    # Si no hubo coincidencias
    if len(df) == 0:
        # 1. Buscar por club, nombre del jugador (sin caracteres fuera del ascii)
        df = dataTMarkt.loc[(dataTMarkt['Squad'] == dataPlayerFBref['Squad']) &
                            (dataTMarkt['Player'].apply(unidecode) == unidecode(player))]

    # Si no hubo coincidencias
    if len(df) == 0:
        # 2. Buscar por club, año de nacimiento
        df = dataTMarkt.loc[(dataTMarkt['Squad'] == dataPlayerFBref['Squad']) &
                            (dataTMarkt['Born'] == dataPlayerFBref['Born'])]
        if len(df) > 1:
            # 2.1 Si al aplicar este filtro, hay algun jugador con gran similitud en su nombre, cogerlo y salir
            df["Player_dist"] = df.apply(lambda row: SequenceMatcher(None, player, row["Player"]).ratio(), axis=1)
            p = df.iloc[df["Player_dist"].argmax()]
            if p["Player_dist"] > 0.90:
                player = p["Player"]
                return player
            else:
                df.drop(df.index, inplace=True)

    # Si no hubo coincidencias
    if len(df) == 0:
        # 3. Buscar por club, nacionalidad, año de nacimiento
        df = dataTMarkt.loc[(dataTMarkt['Squad'] == dataPlayerFBref['Squad']) &
                            (dataTMarkt['Nation'] == dataPlayerFBref['Nation']) &
                            (dataTMarkt['Born'] == dataPlayerFBref['Born'])]

    # Si se encontro una unica coincidencia
    if len(df) == 1:
        # Si el nombre de FBRef es igual al nombre de Transfermarkt, salir
        # Si hay diferencias, mirar cuanto de distinto es
        player = df.iloc[0]["Player"]
    elif len(df) > 1:
        df["Player_dist"] = df.apply(lambda row: SequenceMatcher(None, player, row["Player"]).ratio(), axis=1)
        p = df.iloc[df["Player_dist"].argmax()]
        player = p["Player"]

    return player

# Dado un nombre de equipo de los datos de FBRef,
# busca el nombre mas parecido de los datos de Transfermarkt
# de esa temporada, gracias a la distancia de Hamming
# @lru_cache()
def getTFMarktTeamName(teamDataFBRef, teamDataTMarkt):
    team = teamDataFBRef["Squad"]

    # Hay equipos que tienen el nombre muy distinto entre FBRef y Transfermarkt,
    # por lo que hay que mirar si estan en la tabla de mapeos
    if team in TEAM_MAP:
        team = TEAM_MAP.get(team, team)
    else:
        # Filtrar las opciones posibles por liga
        df = teamDataTMarkt.loc[teamDataTMarkt['Comp'] == teamDataFBRef['Comp']]

        # Si se encontro una unica coincidencia
        if len(df) == 1:
            # Si el nombre de FBRef es igual al nombre de Transfermarkt, salir
            # Si hay diferencias, mirar cuanto de distinto es
            team = df.iloc[0]["Squad"]
        elif len(df) > 1:
            df["Team_dist"] = df.apply(
                lambda row: SequenceMatcher(None, teamDataFBRef["Squad"], row["Squad"]).ratio(), axis=1)
            p = df.iloc[df["Team_dist"].argmax()]
            team = p["Squad"]

    return team

def main():
    if len(sys.argv)>2:
        # Primer parametro indica la ruta donde coger los datos estadisticos por temporada (FBRef)
        leagueDir = sys.argv[1]
        # Segundo parametro indica la ruta donde coger los datos de mercado por temporada (Transfermarkt)
        transferMarktDir = sys.argv[2]
        print("Base folder: " + leagueDir)
        # Si el directorio existe
        if os.path.exists(leagueDir):
            # Listar el numero de temporadas que hay de esa liga
            seasons = os.listdir(leagueDir)
            print("Seasons found: " + str(seasons))
            for season in seasons:
                # Realizar limpieza y formateo de datos por temporada
                cleanFBRefStats(leagueDir, transferMarktDir, season)
        else:
            print("Folder '"+ leagueDir +"' not found!!")
    else:
        print("Command error. It must be executed with 'fbref_clean 'path_to_the_league' 'path_to_transfermarkt_data'")

if __name__ == "__main__":
    main()