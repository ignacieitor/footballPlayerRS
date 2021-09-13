import os
from datetime import datetime
from math import sqrt

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn import preprocessing, metrics
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics.pairwise import cosine_similarity
from pycaret.regression import *
from difflib import SequenceMatcher
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Combobox
from pandastable import Table, config

# Constantes con los pesos de los dos modelos
SIMILARITY_IMPORTANCE = 0.99
VALORATION_IMPORTANCE = 0.01

# Minimo valor de tasa de acierto de fichaje para considerarlo relevante
RELEVANT_SUCCESS_RATE = 0.85
# Minimo numero de partidos para considerar a un jugador importante y
# asi poder tenerlo en cuenta para evaluar las recomendaciones
MINIMUM_MATCHES_KEY_PLAYER = 15
# Top K de jugadores recomendados durante la evaluacion
# De momento coger todos
TOP_K_EVALUATION = 3000 # 500

# Variable global para el dataset
data = None
# Variable global para la ruta del dataset cargado
dataPath = None

# Funcion que dado un jugador busca por similaridad el id
def findPlayerId(df, playerName, playerSquad):
    df_aux = df.copy()

    df_aux["Team_dist"] = df_aux.apply(
        lambda row: SequenceMatcher(None, playerSquad, row["Squad"]).ratio(), axis=1)
    team = df_aux.iloc[df_aux["Team_dist"].argmax()]["Squad"]

    df_aux["Player_dist"] = df_aux.apply(
        lambda row: SequenceMatcher(None, playerName, row["Player"]).ratio(), axis=1)
    player = df_aux.iloc[df_aux["Player_dist"].argmax()]["Player"]

    id = df_aux.index[(df_aux['Squad'] == team) & (df_aux['Player'] == player)].values.astype(int)[0]

    return team, player, id

# Funcion que dado un jugador devuelve el id
def getPlayerId(df, playerName, playerSquad):
    id = df.index[(df['Squad'] == playerSquad) & (df['Player'] == playerName)].values.astype(int)[0]
    return id

# TODO: Funcion que dado un id te devuelva el jugador

# Funcion que dados los datos de una temporada, calcula las distancias entre jugadores
# gracias a la distancia del coseno
def create_sim_matrix(df):
    df_aux = df.copy()

    # Eliminar atributos que no son relevantes para comparar jugadores
    df_aux.drop(["Player", "Comp", "Squad", "Nation", "Born", "Age", "Value"], axis=1, inplace=True)
    # TODO: En lugar de eliminar atributos se podrian elegir diferentes atributos por posicion del jugador

    # Rellenar nulos con ceros (si los hubiera)
    df_aux.fillna(0, inplace=True)

    # Crear una columna especifica por posicion para una mejor busqueda
    df_aux = pd.get_dummies(df_aux, columns=['Pos'])

    # Normalizar entre 0 y 1 todas las caracteristicas
    scaler = preprocessing.MinMaxScaler()
    d = scaler.fit_transform(df_aux)
    df_aux = pd.DataFrame(d, columns=df_aux.columns)

    # Crear la matriz de similaridad con la distancia coseno
    cosine_sim_matrix = cosine_similarity(df_aux)

    return cosine_sim_matrix

# Funcion que dada una matriz con la distancias entre jugadores,
# devuelve los k mas similares a uno dado
def top_k_similares(cosine_sims, df, playerId, k):
    # Ordenar playerIds por similaridad
    full_sorted_sim_list_by_playerId = np.argsort(-cosine_sims, axis=1)
    # Ordenar por valor de similaridad
    full_sorted_sim_list_by_cosine = -np.sort(-cosine_sims, axis=1)

    # Seleccionar solo los valores del jugador buscado
    sorted_sim_list_by_playerId = full_sorted_sim_list_by_playerId[playerId]
    sorted_sim_list_by_cosine = full_sorted_sim_list_by_cosine[playerId]

    # Recoger solo los K primeros
    top_k = sorted_sim_list_by_playerId[1:k+1]
    cosine_top_k = sorted_sim_list_by_cosine[1:k+1]

    # Preparar la salida cogiendo todas las columnas del dataset original
    # pero de los k mas cercanos, añadiendo el porcentaje de similaridad
    top_k_df = df.iloc[top_k].copy()
    top_k_df["Similarity%"] = cosine_top_k

    return top_k_df

# Funcion auxiliar para el calculo del valor de un jugador
# que creara las columnas del atributo posicion para poder usar
# el modelo predictivo creado
def create_position_cols(df):
    df_aux = df.copy()
    df_aux = pd.get_dummies(df_aux, columns=['Pos'])
    if "Pos_GK" not in df_aux.columns:
        df_aux["Pos_GK"] = 0
    if "Pos_DF" not in df_aux.columns:
        df_aux["Pos_DF"] = 0
    if "Pos_MF" not in df_aux.columns:
        df_aux["Pos_MF"] = 0
    if "Pos_FW" not in df_aux.columns:
        df_aux["Pos_FW"] = 0

    return df_aux

# Funcion auxiliar para el calculo del valor de un jugador
# que creara las columnas del atributo liga para poder usar
# el modelo predictivo creado
def create_competition_cols(df):
    df_aux = df.copy()
    df_aux = pd.get_dummies(df_aux, columns=['Comp'])
    if "Comp_La Liga" not in df_aux.columns:
        df_aux["Comp_La Liga"] = 0
    if "Comp_Bundesliga" not in df_aux.columns:
        df_aux["Comp_Bundesliga"] = 0
    if "Comp_Premier League" not in df_aux.columns:
        df_aux["Comp_Premier League"] = 0
    if "Comp_Ligue 1" not in df_aux.columns:
        df_aux["Comp_Ligue 1"] = 0
    if "Comp_Serie A" not in df_aux.columns:
        df_aux["Comp_Serie A"] = 0

    return df_aux

# Funcion que calcula la valoracion negativa / positiva de un jugador
# respecto a su valoracion real en el mercado. El valor estara siempre entre -1 y 1:
# -1 --> Jugador sobrevalorado
#  1 --> Jugador infravalorado
def calculate_valoration(player):
    # Hay jugadores de los que no se dispone de valor de mercado
    if player["Value"] == 0:
        desv = 1
    else:
        desv = player["Predicted Value"] / player["Value"]
    if desv >= 1:
        val = 1
    elif desv < -1:
        val = -1
    else:
        val = desv - 1
    # if desv < -1 or desv > 1:
    #     val = desv
    # else:
    #     val = desv - 1

    return val

def formatValue(x):
    return "€{:,.0f}".format(int(x))

# Funcion que calcula el valor de los jugadores pasados gracias al modelo predictivo cargado
# devolviendo su valor predicho y su valoracion positiva o negativa
def calculate_market_value(model, df):
    df_aux = df.copy()

    # Preparar los datos para pasarselos al modelo creado
    df_aux = create_position_cols(df_aux)
    df_aux = create_competition_cols(df_aux)
    df_aux.dropna(subset=['Value'], inplace=True)
    df_aux.fillna(0, inplace=True)

    # Calcular el valor del jugador en funcion de datos pasados
    preds = predict_model(model, data=df_aux)

    preds["Predicted Value"] = np.exp(preds["Label"])
    preds["Valoration"] = preds.apply(lambda row: calculate_valoration(row), axis=1)

    # Formatear campos de valores de mercado
    preds["Value"] = preds["Value"].apply(formatValue)
    preds["Predicted Value"] = preds["Predicted Value"].apply(formatValue)

    return preds

# % Acierto de fichaje = Similaridad * SIMILARITY_IMPORTANCE + (Predicted Value / Value - 1) * VALORATION_IMPORTANCE
def calculate_success_rate(player):
    # if player["Valoration"] >= 1:
    #     val = 1
    # elif player["Valoration"] < -1:
    #     val = -1
    # else:
    #     val = player["Valoration"]
    # return player["Similarity%"] * SIMILARITY_IMPORTANCE + val * VALORATION_IMPORTANCE
    return player["Similarity%"] * SIMILARITY_IMPORTANCE + player["Valoration"] * VALORATION_IMPORTANCE

def undumify_position(player):
    position = ""
    if player["Pos_GK"]:
        position = "GK"
    elif player["Pos_DF"]:
        position = "DF"
    elif player["Pos_MF"]:
        position = "MF"
    elif player["Pos_FW"]:
        position = "FW"
    return position

def getSimilarPlayers(df, playerId, k):
    # print("start getSimilarPlayers - " + str(datetime.now()))
    # Crear la matriz de similaridad
    cos_sims = create_sim_matrix(df)
    # print("after create_sim_matrix - " + str(datetime.now()))

    # Obtener lista de jugadores similares
    df_top_k = top_k_similares(cos_sims, df, playerId, k)
    # print("after top_k_similares - " + str(datetime.now()))

    # Cargar el modelo predictivo del valor de mercado
    Pred_Value_model = load_model('./Models/model_210810', verbose=False)
    # print("after load_model - " + str(datetime.now()))
    # Predecir valoracion
    df_top_k_value = calculate_market_value(Pred_Value_model, df_top_k)
    # print("after calculate_market_value - " + str(datetime.now()))

    # Calcular el porcentaje de acierto (ponderando similaridad + valoracion)
    df_top_k_value["Success%"] = df_top_k_value.apply(lambda row: calculate_success_rate(row), axis=1)

    # Crear nuevamente la columna posicion
    # df_top_k_value["Pos"] = df_top_k_value.apply(lambda row: undumify_position(row), axis=1)

    # Ordenar
    final_recommendations = df_top_k_value.sort_values(["Success%"], ascending=False)[["Player", "Squad", "Similarity%", "Value", "Predicted Value", "Valoration", "Success%"]]
    # final_recommendations = df_top_k_value.sort_values(["Success%"], ascending=False)[
    #     ["Player", "Pos", "Squad", "Similarity%", "Value", "Predicted Value", "Valoration", "Success%"]]

    # print("exit getSimilarPlayers - " + str(datetime.now()))
    return final_recommendations

# Este metodo calcula la relevancia de solo los jugadores titulares de la misma posicion
# y devuelve el de mayor relevancia
def calculate_relevance_old(dfStats, playerIn, squadIn, positionIn, top_k, max_success):
    relevant = False
    max_successRate = 0
    max_successRatePlayer = ""
    # Hacer filtro en los datos del año anterior por club y posicion de antes
    # Y que sean de los que más juegan (mas de n partidos completos por año)
    playersOut = dfStats.loc[(dfStats["Squad"] == squadIn) & (dfStats["Pos"] == positionIn) &
                             (dfStats["Min/90"] > MINIMUM_MATCHES_KEY_PLAYER)]
    # playersOut = dfStats.loc[(dfStats["Squad"] == squadIn) &
    #                          (dfStats["Min/90"] > MINIMUM_MATCHES_KEY_PLAYER)]
    if max_success:
        # Recorrer todos los jugadores encontrados y hacer recomendaciones sobre ellos
        for j in range(len(playersOut)):
            # Recoger nombre y covertirlo a ID
            playerOut = playersOut.iloc[j]["Player"]
            playerOutId = getPlayerId(dfStats, playerOut, squadIn)
            df_rec = getSimilarPlayers(dfStats, playerOutId, top_k)

            # Buscar jugador en las recomendaciones
            playerFound = df_rec.loc[df_rec["Player"] == playerIn]
            if len(playerFound) > 0:
                successRate = playerFound["Success%"].values[0]
                # Si se supero el maximo conseguido hasta ahora
                if successRate > max_successRate:
                    max_successRate = successRate
                    max_successRatePlayer = playerOut
        # Si el valor de acierto de fichaje es superior a X, se considera relevante
        if max_successRate > RELEVANT_SUCCESS_RATE:
            relevant = True
            print("YES (" + max_successRatePlayer + " - " + str(round(max_successRate, 2)) + ")")
    else:
        # Recorrer todos los jugadores encontrados y hacer recomendaciones sobre ellos
        for j in range(len(playersOut)):
            # Recoger nombre y covertirlo a ID
            playerOut = playersOut.iloc[j]["Player"]
            playerOutId = getPlayerId(dfStats, playerOut, squadIn)
            df_rec = getSimilarPlayers(dfStats, playerOutId, top_k)

            # Buscar jugador en las recomendaciones
            playerFound = df_rec.loc[df_rec["Player"] == playerIn]
            if len(playerFound) > 0:
                successRate = playerFound["Success%"].values[0]
                # Si el valor de acierto de fichaje es superior a X, se considera relevante
                if successRate > RELEVANT_SUCCESS_RATE:
                    max_successRate = max_successRate
                    max_successRatePlayer = playerOut
                    relevant = True
                    print("YES (" + playerOut + " - " + str(round(successRate, 2)) + ")")
                    break

    if not relevant:
        print("NO")

    return relevant, max_successRatePlayer, max_successRate

# Este metodo calcula la relevancia de todos los jugadores titulares devolviendo una tabla
# con todos los jugadores analizandos indicando si fue o no relevante la recomendacion
def calculate_relevance(dfStats, playerIn, squadIn, positionIn, top_k):
    dfPlayer = pd.DataFrame(columns = ["PlayerIn", "SquadIn", "PosIn", "PlayerOut", "PosOut",
                                       "Relevant", "PredRelevant", "PredSuccess%"])
    i = 0

    # Hacer filtro en los datos del año anterior por club y que
    # sean de los que más juegan (mas de n partidos completos por año)
    playersOut = dfStats.loc[(dfStats["Squad"] == squadIn) &
                             (dfStats["Min/90"] > MINIMUM_MATCHES_KEY_PLAYER)]

    # Recorrer todos los jugadores encontrados y hacer recomendaciones sobre ellos
    for j in range(len(playersOut)):
        # Recoger nombre y covertirlo a ID
        playerOut = playersOut.iloc[j]["Player"]
        playerOutId = getPlayerId(dfStats, playerOut, squadIn)
        positionOut = playersOut.iloc[j]["Pos"]
        # Definimos ground truth (si misma posicion relevante, sino no)
        relevant = True if positionOut == positionIn else False
        # Hacer recomendacion
        df_rec = getSimilarPlayers(dfStats, playerOutId, top_k)

        predRelevant = False
        predSuccessRate = 0
        # Buscar jugador en las recomendaciones
        playerFound = df_rec.loc[df_rec["Player"] == playerIn]
        if len(playerFound) > 0:
            predSuccessRate = playerFound["Success%"].values[0]
            # Si el valor de acierto de fichaje es superior a X, se considera relevante
            if predSuccessRate > RELEVANT_SUCCESS_RATE:
                predRelevant = True

        if predRelevant == True:
            print("YES (" + playerOut + " - " + str(predSuccessRate) + ")")
        else:
            print("NO (" + playerOut + " - " + str(predSuccessRate) + ")")

        dfPlayer.loc[i] = [playerIn, squadIn, positionIn, playerOut, positionOut,
                           relevant, predRelevant, predSuccessRate]
        i = i+1

    return dfPlayer

def evaluate_transfers(dfStats, dfTransfers, season, top_k):
    print(season + " TRANSFERS EVALUATION")
    print("-------------------------")
    dfResults = dfTransfers.copy()
    dfPlayersResults = None
    # dfResults["Relevant"] = False
    # Por cada jugador fichado, obtener el club que ficha y la posicion
    for i in range(len(dfTransfers)):
        try:
            playerIn = dfTransfers.loc[i, "PlayerIn"]
            squadIn = dfTransfers.loc[i, "SquadIn"]
            positionIn = dfTransfers.loc[i, "PosIn"]
            print("Player " + str(i + 1) + " from " + str(
                len(dfTransfers)) + " - " + playerIn + "(" + squadIn + "):")
            # Calcular si el fichaje es una recomendacion relevante por el sistema
            # dfResults.at[i, ['Relevant', 'RelevantPlayer', 'RelevantSuccess%']] = calculate_relevance_old(dfStats, playerIn, squadIn, positionIn, top_k, True)
            dfPlayerResults = calculate_relevance(dfStats, playerIn, squadIn, positionIn, top_k)
            if dfPlayersResults is None:
                dfPlayersResults = dfPlayerResults
            else:
                dfPlayersResults = dfPlayersResults.append(dfPlayerResults, ignore_index=True)

        except:
            print("Error processing player " + str(i + 1) + " from " + str(len(dfTransfers)))

    # Merger dfResults con dfPlayerResults
    dfResults = pd.merge(dfResults, dfPlayersResults, how='outer', on=["PlayerIn", "SquadIn", "PosIn"])
    return dfResults

def plot_simple_matrix_confusion(cf_matrix):
    sns.heatmap(cf_matrix, annot=True, xticklabels=['Positive', 'Negative'],
                yticklabels=['Positive', 'Negative'])
    plt.ylabel("Label")
    plt.xlabel("Predicted")
    plt.show()

def make_confusion_matrix(cf,
                          group_names=None,
                          categories='auto',
                          count=True,
                          percent=True,
                          cbar=True,
                          xyticks=True,
                          xyplotlabels=True,
                          sum_stats=True,
                          figsize=None,
                          cmap='Blues',
                          title=None):
    '''
    This function will make a pretty plot of an sklearn Confusion Matrix cm using a Seaborn heatmap visualization.
    Arguments
    ---------
    cf:            confusion matrix to be passed in
    group_names:   List of strings that represent the labels row by row to be shown in each square.
    categories:    List of strings containing the categories to be displayed on the x,y axis. Default is 'auto'
    count:         If True, show the raw number in the confusion matrix. Default is True.
    normalize:     If True, show the proportions for each category. Default is True.
    cbar:          If True, show the color bar. The cbar values are based off the values in the confusion matrix.
                   Default is True.
    xyticks:       If True, show x and y ticks. Default is True.
    xyplotlabels:  If True, show 'True Label' and 'Predicted Label' on the figure. Default is True.
    sum_stats:     If True, display summary statistics below the figure. Default is True.
    figsize:       Tuple representing the figure size. Default will be the matplotlib rcParams value.
    cmap:          Colormap of the values displayed from matplotlib.pyplot.cm. Default is 'Blues'
                   See http://matplotlib.org/examples/color/colormaps_reference.html

    title:         Title for the heatmap. Default is None.
    '''

    # CODE TO GENERATE TEXT INSIDE EACH SQUARE
    blanks = ['' for i in range(cf.size)]

    if group_names and len(group_names) == cf.size:
        group_labels = ["{}\n".format(value) for value in group_names]
    else:
        group_labels = blanks

    if count:
        group_counts = ["{0:0.0f}\n".format(value) for value in cf.flatten()]
    else:
        group_counts = blanks

    if percent:
        group_percentages = ["{0:.2%}".format(value) for value in cf.flatten() / np.sum(cf)]
    else:
        group_percentages = blanks

    box_labels = [f"{v1}{v2}{v3}".strip() for v1, v2, v3 in zip(group_labels, group_counts, group_percentages)]
    box_labels = np.asarray(box_labels).reshape(cf.shape[0], cf.shape[1])

    # CODE TO GENERATE SUMMARY STATISTICS & TEXT FOR SUMMARY STATS
    if sum_stats:
        # Accuracy is sum of diagonal divided by total observations
        accuracy = np.trace(cf) / float(np.sum(cf))

        # if it is a binary confusion matrix, show some more stats
        if len(cf) == 2:
            # Metrics for Binary Confusion Matrices
            precision = cf[0, 0] / sum(cf[:, 0])
            recall = cf[0, 0] / sum(cf[0, :])
            f1_score = 2 * precision * recall / (precision + recall)
            stats_text = "\n\nAccuracy={:0.3f}\nPrecision={:0.3f}\nRecall={:0.3f}\nF1 Score={:0.3f}".format(
                accuracy, precision, recall, f1_score)
        else:
            stats_text = "\n\nAccuracy={:0.3f}".format(accuracy)
    else:
        stats_text = ""

    # SET FIGURE PARAMETERS ACCORDING TO OTHER ARGUMENTS
    if figsize == None:
        # Get default figure size if not set
        figsize = plt.rcParams.get('figure.figsize')

    if xyticks == False:
        # Do not show categories if xyticks is False
        categories = False

    # MAKE THE HEATMAP VISUALIZATION
    plt.figure(figsize=figsize)
    sns.heatmap(cf, annot=box_labels, fmt="", cmap=cmap, cbar=cbar, xticklabels=categories, yticklabels=categories)

    if xyplotlabels:
        plt.ylabel('True label')
        plt.xlabel('Predicted label' + stats_text)
    else:
        plt.xlabel(stats_text)

    if title:
        plt.title(title)

    plt.show()

# Funcion que dados dos dataframe de predicciones y resultados esperados
# calculara las metricas más comunes como MAE, MSE y RMSE
def get_standard_metrics(preds, actuals):
    p = preds.values.flatten()
    a = actuals.values.flatten()

    mae = metrics.mean_absolute_error(p, a)
    mse = metrics.mean_squared_error(p, a)
    rmse = sqrt(mse)

    return mae, mse, rmse

def main():
    root = Tk()
    root.title("Football Player RS")
    photo = PhotoImage(file="app_icon.png")
    root.iconphoto(True, photo)
    windowWidth = 800
    windowHeight = 500
    root.geometry('{}x{}'.format(windowWidth, windowHeight))

    # Centrar la ventana en la pantalla
    positionRight = int(root.winfo_screenwidth() / 2 - windowWidth / 2)
    positionDown = int(root.winfo_screenheight() / 2 - windowHeight / 2)
    root.geometry("+{}+{}".format(positionRight, positionDown))

    # Texto para guiar al usuario a cargar los datos
    Label(root, text="Select and load the football player dataset:").place(x=20, y=5)

    # Frame donde se mostrara la tabla de resultados
    frame = Frame(root)
    # frame.place(x=20, y=200)
    frame.pack(fill='x', side=BOTTOM)

    # Input para cambiar manual o automaticamente la ruta del dataset de entrada
    e = StringVar()
    Entry(root, textvariable=e, width=100).place(x=20,y=25)
    # TODO: Eliminar esta asignacion. Solo esta para agilizar las pruebas
    e.set("D:/Nacho/Universidad/UNIR/Cuatrimestre 2/TFM/PyCharm/Transfermarkt/fbref_transfermarkt_2017_2018.csv")


    # Evento del boton de seleccionar el dataset
    def btn_select_data_clicked():
        # Preguntar por la ruta del dataset a cargar
        file = filedialog.askopenfilename(filetypes=(("CSV files", "*.csv"),))
        e.set(file)

    # Evento del boton de cargar el dataset
    def btn_load_data_clicked():
        global dataPath
        dataPath = e.get()
        try:
            global data
            data = pd.read_csv(dataPath, encoding="utf8")
            comboSquads['values'] = sorted(data["Squad"].unique())
            comboSquads.current(0)
        except:
            messagebox.showerror('Error', 'Dataset cannot be loaded')

    # Botones para la gestion de la seleccion y carga del dataset
    Button(root, text="Select data", bg='#0052cc', fg='#ffffff',
           command=btn_select_data_clicked).place(x=630, y=23)
    Button(root, text="Load data", bg='#0052cc', fg='#ffffff',
           command=btn_load_data_clicked).place(x=700, y=23)

    Label(root, text="Choose the player to replace:").place(x=20, y=50)
    # Combo que contendra los equipos disponibles del dataset
    def comboSquads_dropdown():
        try:
            comboSquads['values'] = sorted(data["Squad"].unique())
            comboPlayers.set('')
        except:
            messagebox.showerror('Error', 'First load a football player dataset')
    def comboSquads_selected(eventObject):
        squadSelected = comboSquads.get()
        comboPlayers['values'] = sorted(data[data["Squad"] == squadSelected]["Player"])
        comboPlayers.current(0)

    Label(root, text="Squad: ").place(x=20, y=75)
    comboSquads = Combobox(root, state="readonly", width=25, postcommand=comboSquads_dropdown)
    comboSquads.place(x=70, y=75)
    comboSquads.bind("<<ComboboxSelected>>", comboSquads_selected)
    # Combo que contendra los equipos disponibles del dataset
    def comboPlayers_dropdown():
        try:
            squadSelected = comboSquads.get()
            comboPlayers['values'] = sorted(data[data["Squad"]==squadSelected]["Player"])
        except:
            messagebox.showerror('Error', 'First load a football player dataset')
    Label(root, text="Player: ").place(x=250, y=75)
    comboPlayers = Combobox(root, state="readonly", width=25, postcommand=comboPlayers_dropdown)
    comboPlayers.place(x=300, y=75)

    Label(root, text="Top K: ").place(x=480, y=75)
    top_k = StringVar()
    sb_top_k = Spinbox(root, width=5, from_=0, to=100, textvariable=top_k)
    sb_top_k.place(x=525, y=75)
    top_k.set(50)

    lbl_results = Label(root, text="", font=('Arial', 9, 'bold', 'underline'))
    lbl_results.place(x=20, y=165)

    # Evento del boton de recomendar jugadores
    def btn_show_similar_players_clicked():
        # Obtener el equipo seleccionado
        squadSelected = comboSquads.get()
        # Obtener el jugador seleccionado
        playerSelected = comboPlayers.get()
        # Si alguno de los dos es vacio, mostrar error
        if squadSelected == "" or playerSelected == "":
            messagebox.showerror('Error', 'Please select the player first')
        else:
            try:
                playerId = getPlayerId(data, playerSelected, squadSelected)
                # Obtener los k primeros que diga el usuario
                k = int(sb_top_k.get())
                lbl_results.configure(text=str(k)+" SIMILAR PLAYERS TO " +
                                           str.upper(playerSelected) + " (" + str.upper(squadSelected) + "):")
                df_rec = getSimilarPlayers(data, playerId, k)
                pt = Table(frame, dataframe=df_rec, editable=False)
                options = {'colheadercolor': '#0052cc', 'fontsize': 8}
                config.apply_options(options, pt)
                pt.show()
                pt.redraw()
            except:
                messagebox.showerror('Error', 'Error getting similar players')

    # Boton para realizar la recomendacion
    Button(root, text="Show recommended players", width=23, bg='#0052cc', fg='#ffffff',
           command=btn_show_similar_players_clicked).place(x=300, y=120)

    # Evento del boton de evaluar SR
    def btn_evaluate_rs_clicked():
        try:
            # Recoger los fichajes de un año determinado
            if dataPath != None:
                # Coger la temporada que finaliza para poder recoger despues los fichajes de ese año
                season = dataPath.split(".")[0][-4:]
                parent = os.path.dirname(dataPath)
                transfers_df = pd.read_csv(os.path.join(parent, "transfermarkt_transfers_" + season + ".csv"), encoding="utf8")
                df_results = evaluate_transfers(data, transfers_df, season, TOP_K_EVALUATION)
                # Guardar en disco
                resultsFilePath = os.path.join(parent, "results_rs_" + season + ".csv")
                df_results.to_csv(resultsFilePath, index=False)
                print("Evaluation for " + season + " transfers done!!")
            else:
                confirm = messagebox.askyesnocancel(
                    title="Question",
                    message="Do you want only get metrics?",
                    default=messagebox.YES)
                if confirm:
                    season = "2018"
                    parent = ".//Transfermarkt"
                    results_df = pd.read_csv(os.path.join(parent, "results_rs_" + season + ".csv"),
                                               encoding="utf8")
                    results_same_pos_df = results_df.loc[results_df["PosIn"] == results_df["PosOut"]]
                    get_standard_metrics(results_same_pos_df["PredSuccess%"], pd.Series([RELEVANT_SUCCESS_RATE]).repeat(len(results_same_pos_df)))
                    # Get the confusion matrix
                    # cf_matrix = confusion_matrix(results_df["Relevant"], results_df["PredRelevant"], labels=[1,0])
                    # labels = ["TP", "FN", "FP", "TN"]
                    # categories = ["Relevant", "No Relevant"]
                    # make_confusion_matrix(cf_matrix, group_names=labels, categories=categories, percent=False)

                elif confirm is None:
                    print("Press CANCEL")
                else:
                    print("Press NO")
                    # # Si no se selecciono el año en cuestion, evaluar todos los años
                    # for i in range(2017, 2021):
                    #     season = str(i+1)
                    #     parent = ".//Transfermarkt"
                    #     transfers_df = pd.read_csv(os.path.join(parent, "transfermarkt_transfers_" + season + ".csv"),
                    #                                encoding="utf8")
                    #     data_df = pd.read_csv(os.path.join(parent, "fbref_transfermarkt_" + str(i) + "_" + str(season) + ".csv"),
                    #                                encoding="utf8")
                    #     df_results = evaluate_transfers(data_df, transfers_df, season, TOP_K_EVALUATION)
                    #     # Guardar en disco
                    #     resultsFilePath = os.path.join(parent, "results_rs_" + season + ".csv")
                    #     df_results.to_csv(resultsFilePath, index=False)
                    #     print("Evaluation for " + season + " transfers done!!")
        except:
            messagebox.showerror('Error', 'Dataset cannot be loaded for the evaluation')

    # Boton para realizar la evaluacion
    Button(root, text="Evaluate RS", width=23, bg='#0052cc', fg='#ffffff',
           command=btn_evaluate_rs_clicked).place(x=500, y=120)

    root.mainloop()

    # if len(sys.argv)>1:
    #     # Primer parametro indica la temporada desde la que se desean obtener jugadores
    #     season = sys.argv[1]
    #
        # # Cargar dataset del año deseado
        # data = pd.read_csv("./Transfermarkt/fbref_" + season + "_transfermarkt.csv")
        #
        # # Crear la matriz de similaridad
        # cos_sims = create_sim_matrix(data)
        #
        # playerSquad, playerName, playerId = findPlayerId(data, "Leo Messi", "Barcelona")
        # # Pedir el jugador a reemplazar
        # # playerId = 1453     # Messi
        # # playerId = 1066     # Oblak
        # # playerId = 1352     # De Bruyne
        # # playerId = 452      # Cristiano Ronaldo
        # # playerId = 849      # Pique
        # # playerId = 2332     # Ramos
        # # playerId = 482      # Parejo
        #
        # # Numero de resultados
        # k = 50
        #
        # # Obtener lista de jugadores similares
        # df_top_k = top_k_similares(cos_sims, data, playerId, k)
        #
        # # Cargar el modelo predictivo del valor de mercado
        # Predicted Value_model = load_model('./Models/model_210810')
        #
        # # Predecir valoracion
        # df_top_k_value = calculate_market_value(Predicted Value_model, df_top_k)
        #
        # # Calcular el porcentaje de acierto (ponderando similaridad + valoracion)
        # df_top_k_value["Success%"] = df_top_k_value.apply(lambda row: calculate_success_rate(row), axis=1)
        #
        # # Ordenar
        # final_recommendations = df_top_k_value.sort_values(["Success%"], ascending=False)[["Player", "Squad", "Value", "Predicted Value", "Valoration", "Similarity%", "Success%"]]
        #
        # print(str(k) + " similar players to " + playerName + " (" + playerSquad + "):")
        # print(final_recommendations.to_string())
    # else:
    #     print("Command error. It must be executed with ' RS 'season' '. Example: RS.py 2020_2021")
    #
    # return

if __name__ == "__main__":
    main()