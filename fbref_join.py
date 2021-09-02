import os
import sys
import pandas as pd

# Junta las diferentes tipos de estadisticas (ofensivas, defensivas, de pases, de porteros, etc.) en un unico dataset
def joinStats(leagueDir, season):
    seasonDir = os.path.join(leagueDir, season, "out")
    statFiles = os.listdir(seasonDir)
    print("Stats found for season '" + season + "': " + str(statFiles))
    joinedFilePath = None
    dataJoined = None
    for i in range(0, len(statFiles) - 1):
        commonCols = list()
        if joinedFilePath == None:
            currentFilePath = os.path.join(seasonDir, statFiles[i])
        else:
            currentFilePath = joinedFilePath
        nextFilePath = os.path.join(seasonDir, statFiles[i + 1])
        fC = open(currentFilePath, "r", encoding='utf8')
        fN = open(nextFilePath, "r", encoding='utf8')
        headerC = fC.readline().rstrip('\n')
        headerN = fN.readline().rstrip('\n')
        fC.close()
        fN.close()
        colsC = headerC.split(",")
        colsN = headerN.split(",")
        # Eliminar el identificador de jugador ya que a veces no coincide con el mismo jugador en las diferentes tablas
        if "Rk" in colsC:
            colsC.remove("Rk")
        if "Rk" in colsN:
            colsN.remove("Rk")
        if currentFilePath.endswith("_Goalkeeping.csv"):
            # MP,Starts,Min,Min/90
            if "MP" in colsC:
                colsC.remove("MP")
            if "Starts" in colsC:
                colsC.remove("Starts")
            if "Min" in colsC:
                colsC.remove("Min")
            if "Min/90" in colsC:
                colsC.remove("Min/90")

        if nextFilePath.endswith("_Goalkeeping.csv"):
            # MP,Starts,Min,Min/90
            if "MP" in colsN:
                colsN.remove("MP")
            if "Starts" in colsN:
                colsN.remove("Starts")
            if "Min" in colsN:
                colsN.remove("Min")
            if "Min/90" in colsN:
                colsN.remove("Min/90")
        for c in colsC:
            if c in colsN:
                commonCols.append(c)
        print(str(len(commonCols)) + " columnas comunes: " + str(commonCols))
        dataC = pd.read_csv(currentFilePath, encoding='utf8')
        dataN = pd.read_csv(nextFilePath, encoding='utf8')
        # Eliminar el identificador de jugador ya que a veces no coincide con el mismo jugador en las diferentes tablas
        if "Rk" in dataC:
            dataC = dataC.drop(['Rk'], axis=1)
        if "Rk" in dataN:
            dataN = dataN.drop(['Rk'], axis=1)

        if currentFilePath.endswith("_Goalkeeping.csv"):
            dataC = dataC.drop(["MP", "Starts", "Min", "Min/90"], axis=1)
        if nextFilePath.endswith("_Goalkeeping.csv"):
            dataN = dataN.drop(["MP", "Starts", "Min", "Min/90"], axis=1)
        dataJoined = pd.merge(dataC, dataN, how='outer', on=commonCols)
        joinedFilePath = os.path.join(seasonDir,  "fbref_" + season + "_joined.csv")
        dataJoined.to_csv(joinedFilePath, index=False)
    # Nueva columna con el id de jugador
    # dataJoined.insert(loc=0, column='playerID', value=dataJoined.index)
    dataJoined.to_csv(joinedFilePath, index=False)
    print("Stats for season '" + season + "' merged in '" + joinedFilePath + "'")
    return joinedFilePath

# Funcion que divide dos numeros teniendo en cuenta que el denominador no sea cero
def my_division(num, den):
    if den > 0:
        return num / den
    else:
        return 0

# Junta las estadisticas de aquellos jugadores que han jugado en dos equipos en el mismo año
def joinDuplicatedPlayers(statsFilePath):
    # Definir campos que miden frecuencia o probabilidad (%regates, %pases, etc.)
    FREQ_FIELDS = ["TklDr%", "Press%", "GA/90", "Save%", "CS%",
                   "PK%", "SCA/90", "GCA/90", "AWon%", "P_Cmp%",
                   "PS_Cmp%", "PM_Cmp%", "PL_Cmp%", "DribSucc%", "Rec%",
                   "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT",
                   "npxG/Sh", "Gls/90", "Ast/90", "G+A/90", "G-PK/90",
                   "G+A-PK/90", "xG/90", "xA/90", "xG+xA/90", "npxG/90",
                   "npxG+xA/90"]
    # Definir campos donde coger primero (nombre, edad, año nacimiento, equipo)
    PERSONAL_FIELDS = ["Pos", "Squad", "Comp", "Born"]

    # Definir campos donde hacer la media
    AVERAGE_FIELDS = ["Dist"]

    # Campos clave para agrupar despues
    KEY_FIELDS = ['Player', 'Nation', 'Age']

    # Cargar el dataset
    data = pd.read_csv(statsFilePath, encoding='utf8')

    # Para usar la funcion agg despues de agrupar, es necesario crear un diccionario donde se especifique que se desea hacer con cada columna
    # Algunas columnas se sumaran, otras se hara la media y en algunas se cogera el primero
    dictColFunction = {}
    for c in data.columns.tolist():
        if c in KEY_FIELDS:
            continue
        elif c in FREQ_FIELDS or c in PERSONAL_FIELDS:
            dictColFunction[c] = "first"
        elif c in AVERAGE_FIELDS:
            dictColFunction[c] = "mean"
        else:
            dictColFunction[c] = "sum"

    # Agrupar por los campos clave y hacer las operaciones concretas con el resto de columnas
    data_no_duplicates = data.groupby(KEY_FIELDS, as_index=False).agg(dictColFunction)

    # El valor por debajo de 1 de la columna "Min/90" hace que algunas estadisticas se disparen, por lo que mejor redondear esa columna
    data_no_duplicates.loc[data_no_duplicates["Min/90"] < 1.0, "Min/90"] = data_no_duplicates["Min/90"].round()

    # Calcular de nuevo los campos promedio (evitando la division por 0)
    # Se ponen a cero algunos estadisticos para evitar que jugadores que hayan jugado poco, tengan valores altos en sus promedios
    data_no_duplicates["TklDr%"] = 0
    data_no_duplicates.loc[data_no_duplicates["TklDrAtt"] > 0.0, "TklDr%"] = data_no_duplicates["TklDr"] / \
                                                                             data_no_duplicates["TklDrAtt"] * 100
    data_no_duplicates["Press%"] = 0
    data_no_duplicates.loc[data_no_duplicates["PressAtt"] > 0.0, "Press%"] = data_no_duplicates["PressSucc"] / \
                                                                             data_no_duplicates["PressAtt"] * 100
    data_no_duplicates["GA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "GA/90"] = data_no_duplicates["GA"] / \
                                                                          data_no_duplicates["Min/90"]
    data_no_duplicates["Save%"] = 0
    data_no_duplicates.loc[data_no_duplicates["SoTA"] > 0.0, "Save%"] = (data_no_duplicates["SoTA"]-data_no_duplicates["GA"]) / \
                                                                        data_no_duplicates["SoTA"] * 100
    data_no_duplicates["CS%"] = 0
    data_no_duplicates.loc[data_no_duplicates["Starts"] > 0.0, "CS%"] = data_no_duplicates["CS"] / \
                                                                        data_no_duplicates["Starts"] * 100
    data_no_duplicates["PK%"] = 0
    data_no_duplicates.loc[data_no_duplicates["PKA"] > 0.0, "PK%"] = data_no_duplicates["PKsv"] / \
                                                                     data_no_duplicates["PKA"] * 100
    data_no_duplicates["SCA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "SCA/90"] = data_no_duplicates["SCA"] / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["GCA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "GCA/90"] = data_no_duplicates["GCA"] / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["AWon%"] = 0
    data_no_duplicates.loc[(data_no_duplicates["AWon"] + data_no_duplicates["ALost"]) > 0.0, "AWon%"] = data_no_duplicates["AWon"] / \
                                                                                                        (data_no_duplicates["AWon"] + data_no_duplicates["ALost"]) * 100
    data_no_duplicates["P_Cmp%"] = 0
    data_no_duplicates.loc[data_no_duplicates["P_Att"] > 0.0, "P_Cmp%"] = data_no_duplicates["P_Cmp"] / \
                                                                          data_no_duplicates["P_Att"] * 100
    data_no_duplicates["PS_Cmp%"] = 0
    data_no_duplicates.loc[data_no_duplicates["PS_Att"] > 0.0, "PS_Cmp%"] = data_no_duplicates["PS_Cmp"] / \
                                                                            data_no_duplicates["PS_Att"] * 100
    data_no_duplicates["PM_Cmp%"] = 0
    data_no_duplicates.loc[data_no_duplicates["PM_Att"] > 0.0, "PM_Cmp%"] = data_no_duplicates["PM_Cmp"] / \
                                                                            data_no_duplicates["PM_Att"] * 100
    data_no_duplicates["PL_Cmp%"] = 0
    data_no_duplicates.loc[data_no_duplicates["PL_Att"] > 0.0, "PL_Cmp%"] = data_no_duplicates["PL_Cmp"] / \
                                                                            data_no_duplicates["PL_Att"] * 100
    data_no_duplicates["DribSucc%"] = 0
    data_no_duplicates.loc[data_no_duplicates["DribAtt"] > 0.0, "DribSucc%"] = data_no_duplicates["DribSucc"] / \
                                                                               data_no_duplicates["DribAtt"] * 100
    data_no_duplicates["Rec%"] = 0
    data_no_duplicates.loc[data_no_duplicates["Targ"] > 0.0, "Rec%"] = data_no_duplicates["Rec"] / \
                                                                       data_no_duplicates["Targ"] * 100
    data_no_duplicates["SoT%"] = 0
    data_no_duplicates.loc[data_no_duplicates["Sh"] > 0.0, "SoT%"] = data_no_duplicates["SoT"] / \
                                                                     data_no_duplicates["Sh"] * 100
    data_no_duplicates["Sh/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "Sh/90"] = data_no_duplicates["Sh"] / \
                                                                          data_no_duplicates["Min/90"]

    data_no_duplicates.loc[data_no_duplicates["Sh"] == 0, "Dist"] = 0

    data_no_duplicates["SoT/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "SoT/90"] = data_no_duplicates["SoT"] / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["G/Sh"] = 0
    data_no_duplicates.loc[data_no_duplicates["Sh"] > 0.0, "G/Sh"] = data_no_duplicates["Gls"] / \
                                                                     data_no_duplicates["Sh"] * 100
    data_no_duplicates["G/SoT"] = 0
    data_no_duplicates.loc[data_no_duplicates["SoT"] > 0.0, "G/SoT"] = data_no_duplicates["Gls"] / \
                                                                       data_no_duplicates["SoT"] * 100
    data_no_duplicates["npxG/Sh"] = 0
    data_no_duplicates.loc[data_no_duplicates["Sh"] > 0.0, "npxG/Sh"] = data_no_duplicates["npxG"] / \
                                                                        data_no_duplicates["Sh"] * 100
    data_no_duplicates["Gls/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "Gls/90"] = data_no_duplicates["Gls"] / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["Ast/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "Ast/90"] = data_no_duplicates["Ast"] / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["G+A/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "G+A/90"] = (data_no_duplicates["Gls"] + data_no_duplicates["Ast"]) / \
                                                                           data_no_duplicates["Min/90"]
    data_no_duplicates["G-PK/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "G-PK/90"] = data_no_duplicates["G-PK"] / \
                                                                            data_no_duplicates["Min/90"]
    data_no_duplicates["G+A-PK/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "G+A-PK/90"] = (data_no_duplicates["Gls"] + data_no_duplicates["Ast"] - data_no_duplicates["PK"]) / \
                                                                              data_no_duplicates["Min/90"]
    data_no_duplicates["xG/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "xG/90"] = data_no_duplicates["xG"] / \
                                                                          data_no_duplicates["Min/90"]
    data_no_duplicates["xA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "xA/90"] = data_no_duplicates["xA"] / \
                                                                          data_no_duplicates["Min/90"]
    data_no_duplicates["xG+xA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "xG+xA/90"] = (data_no_duplicates["xG"] + data_no_duplicates["xA"]) / \
                                                                             data_no_duplicates["Min/90"]
    data_no_duplicates["npxG/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "npxG/90"] = data_no_duplicates["npxG"] / \
                                                                            data_no_duplicates["Min/90"]
    data_no_duplicates["npxG+xA/90"] = 0
    data_no_duplicates.loc[data_no_duplicates["Min/90"] > 0.0, "npxG+xA/90"] = data_no_duplicates["npxG+xA"] / \
                                                                               data_no_duplicates["Min/90"]

    # Redondear todos los valores a dos decimales
    data_no_duplicates = data_no_duplicates.round(decimals=2)

    statsNoDuplicatesFilePath = statsFilePath.replace("_joined.csv", ".csv")
    data_no_duplicates.to_csv(statsNoDuplicatesFilePath, index=False)
    print("Duplicates removed and saved to '" + statsNoDuplicatesFilePath + "'")

def main():
    if len(sys.argv)>1:
        leagueDir = sys.argv[1]
        print("Base folder: " + leagueDir)
        # Si el directorio existe
        if os.path.exists(leagueDir):
            # Listar el numero de temporadas que hay de esa liga
            seasons = os.listdir(leagueDir)
            print("Seasons found: " + str(seasons))
            for season in seasons:
                # Unir las diferentes estadisticas de cada temporada
                joinedFilePath = joinStats(leagueDir, season)
                # Unir estadisticas de jugadores que hayan estado en dos equipos en la misma temporada
                joinDuplicatedPlayers(joinedFilePath)
        else:
            print("Folder '"+ leagueDir +"' not found!!")
    else:
        print("Command error. It must be executed with 'fbref_join 'path_to_the_league'")

if __name__ == "__main__":
    main()



