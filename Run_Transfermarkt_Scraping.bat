@echo off
Rem This script will get the player market values from transfermarkt web in the differents season
Rem La Liga
set ES_LEAGUE="La Liga"
set TRANSFERMARKT_ES_LEAGUE_SEASON=https://www.transfermarkt.com/laliga/startseite/wettbewerb/ES1/plus/?saison_id=
Rem Premier League
set UK_LEAGUE="Premier League"
set TRANSFERMARKT_UK_LEAGUE_SEASON=https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=
Rem Serie A
set IT_LEAGUE="Serie A"
set TRANSFERMARKT_IT_LEAGUE_SEASON=https://www.transfermarkt.com/serie-a/startseite/wettbewerb/IT1/plus/?saison_id=
Rem Bundesliga
set GE_LEAGUE="Bundesliga"
set TRANSFERMARKT_GE_LEAGUE_SEASON=https://www.transfermarkt.com/bundesliga/startseite/wettbewerb/L1/plus/?saison_id=
Rem Ligue 1
set FR_LEAGUE="Ligue 1"
set TRANSFERMARKT_FR_LEAGUE_SEASON=https://www.transfermarkt.com/ligue-1/startseite/wettbewerb/FR1/plus/?saison_id=
Rem Liga NOS
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/liga-nos/startseite/wettbewerb/PO1/plus/?saison_id=
Rem Eredivisie
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/eredivisie/startseite/wettbewerb/NL1/plus/?saison_id=
Rem Premier Liga
rem set TRANSFERMARKT_LEAGUE_SEASON=https://www.transfermarkt.com/premier-liga/startseite/wettbewerb/RU1/plus/?saison_id=

Rem Directory which contains Transfermarkt player data for the diferents seasons
set TRANSFERMARKT_REPOSITORY=Transfermarkt\

SETLOCAL ENABLEDELAYEDEXPANSION
for /l %%x in (2017, 1, 2020) do (
	set /a next_year=%%x+1
	echo Scraping ES player market value from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt.py "chromedriver.exe" %ES_LEAGUE% %TRANSFERMARKT_ES_LEAGUE_SEASON%%%x %TRANSFERMARKT_REPOSITORY%transfermarkt_%%x_!next_year!.csv 
   
	echo Scraping UK player market value from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt.py "chromedriver.exe" %UK_LEAGUE% %TRANSFERMARKT_UK_LEAGUE_SEASON%%%x %TRANSFERMARKT_REPOSITORY%transfermarkt_%%x_!next_year!.csv 
	
	echo Scraping IT player market value from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt.py "chromedriver.exe" %IT_LEAGUE% %TRANSFERMARKT_IT_LEAGUE_SEASON%%%x %TRANSFERMARKT_REPOSITORY%transfermarkt_%%x_!next_year!.csv 
   
	echo Scraping GE player market value from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt.py "chromedriver.exe" %GE_LEAGUE% %TRANSFERMARKT_GE_LEAGUE_SEASON%%%x %TRANSFERMARKT_REPOSITORY%transfermarkt_%%x_!next_year!.csv 	
	
	echo Scraping FR player market value from the year %%x
	C:\Users\Ignacieitor\anaconda3\python.exe scraping_transfermarkt.py "chromedriver.exe" %FR_LEAGUE% %TRANSFERMARKT_FR_LEAGUE_SEASON%%%x %TRANSFERMARKT_REPOSITORY%transfermarkt_%%x_!next_year!.csv 	
)
pause
