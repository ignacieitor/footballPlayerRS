@echo off
Rem This script will get the player market values from transfermarkt web in the differents season
Rem La Liga
set TRANSFERMARKT_ES_LEAGUE_SEASON=https://www.transfermarkt.com/laliga/transfers/wettbewerb/ES1/plus/?saison_id=
Rem Premier League
set TRANSFERMARKT_UK_LEAGUE_SEASON=https://www.transfermarkt.com/premier-league/transfers/wettbewerb/GB1/plus/?saison_id=
Rem Serie A
set TRANSFERMARKT_IT_LEAGUE_SEASON=https://www.transfermarkt.com/serie-a/transfers/wettbewerb/IT1/plus/?saison_id=
Rem Bundesliga
set TRANSFERMARKT_GE_LEAGUE_SEASON=https://www.transfermarkt.com/bundesliga/transfers/wettbewerb/L1/plus/?saison_id=
Rem Ligue 1
set TRANSFERMARKT_FR_LEAGUE_SEASON=https://www.transfermarkt.com/ligue-1/transfers/wettbewerb/FR1/plus/?saison_id=
Rem Liga NOS
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/liga-nos/transfers/wettbewerb/PO1/plus/?saison_id=
Rem Eredivisie
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/eredivisie/transfers/wettbewerb/NL1/plus/?saison_id=
Rem Premier Liga
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/premier-liga/transfers/wettbewerb/RU1/plus/?saison_id=

Rem Directory which contains Transfermarkt player data for the diferents seasons
set TRANSFERMARKT_REPOSITORY=Transfermarkt\
set TRANSFER_SETTINGS=^&s_w^=s^&leihe^=0^&intern^=0
SETLOCAL ENABLEDELAYEDEXPANSION
for /l %%x in (2018, 1, 2021) do (

	echo Scraping ES player transfers from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt_transfers.py "chromedriver.exe" %TRANSFERMARKT_ES_LEAGUE_SEASON%%%x%TRANSFER_SETTINGS% %%x %TRANSFERMARKT_REPOSITORY% %TRANSFERMARKT_REPOSITORY%transfermarkt_transfers%%x.csv 

	echo Scraping UK player transfers from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt_transfers.py "chromedriver.exe" %TRANSFERMARKT_UK_LEAGUE_SEASON%%%x%TRANSFER_SETTINGS% %%x %TRANSFERMARKT_REPOSITORY% %TRANSFERMARKT_REPOSITORY%transfermarkt_transfers%%x.csv 
	
	echo Scraping IT player transfers from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt_transfers.py "chromedriver.exe" %TRANSFERMARKT_IT_LEAGUE_SEASON%%%x%TRANSFER_SETTINGS% %%x %TRANSFERMARKT_REPOSITORY% %TRANSFERMARKT_REPOSITORY%transfermarkt_transfers%%x.csv 
	   
	echo Scraping GE player transfers from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt_transfers.py "chromedriver.exe" %TRANSFERMARKT_GE_LEAGUE_SEASON%%%x%TRANSFER_SETTINGS% %%x %TRANSFERMARKT_REPOSITORY% %TRANSFERMARKT_REPOSITORY%transfermarkt_transfers%%x.csv 
	
	echo Scraping FR player transfers from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt_transfers.py "chromedriver.exe" %TRANSFERMARKT_FR_LEAGUE_SEASON%%%x%TRANSFER_SETTINGS% %%x %TRANSFERMARKT_REPOSITORY% %TRANSFERMARKT_REPOSITORY%transfermarkt_transfers%%x.csv 
)
pause
