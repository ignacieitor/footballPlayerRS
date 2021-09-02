import os
import sys
import pandas as pd

def addMarketValue(dataFbrPath, dataTmarktPath, season):
    # Cargar datos de los estadisticos de FBref
    df_fbr = pd.read_csv(os.path.join(dataFbrPath, season, "out\\fbref_" + season + ".csv"), encoding='utf8')
    # Cargar datos de los valores de mercado de Transfermarkt
    df_tm = pd.read_csv(os.path.join(dataTmarktPath, "transfermarkt_" + season + ".csv"), encoding='utf8')

    # Recuperar el club propietario del jugador a final de temporada (muy util por los fichajes de invierno)
    # Para ello, primero ordenar el dataset por la columna "LastClub" (primero estaran los que no fueron traspasados
    # y despues los que sufrieron traspaso en invierno (valor "true")
	# Eliminar duplicados para quedarse con el ultimo (el segundo con el mismo nombre siempre será "true")
    df_tm = df_tm.sort_values('LastClub').drop_duplicates(subset=['Player', 'Born', 'Nation'], keep='last')

    # Mergear los datos de ambas tablas con la idea de actualizar correctamente liga y club
    df_fbr.drop(['Comp', 'Squad', 'Nation'], axis=1, inplace=True)
    # dataJoined = pd.merge(df_fbr, df_tm[["Player", "Born", "Nation", "Comp", "Squad", "Value"]], how='outer', on=["Player", "Born", "Nation"])
    dataJoined = pd.merge(left = df_fbr, right = df_tm[["Player", "Born", "Nation", "Comp", "Squad", "Value"]],
                          how = "left", left_on=["Player", "Born"], right_on=["Player", "Born"])

    # Eliminar los jugadores que no jugaron ningun minuto
    # dataJoined.dropna(subset=["Pos"], inplace=True)

    # Guardar en disco
    joinedFilePath = os.path.join(dataTmarktPath, "fbref_" + season + "_transfermarkt.csv")
    dataJoined.to_csv(joinedFilePath, index=False)

    return 0

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
                # Añadir el valor de mercado de cada jugador en ese año
                addMarketValue(leagueDir, transferMarktDir, season)
        else:
            print("Folder '"+ leagueDir +"' not found!!")
    else:
        print("Command error. It must be executed with 'fbref_merge_transfermarkt 'path_to_the_league' 'path_to_transfermarkt_data'")

if __name__ == "__main__":
    main()



