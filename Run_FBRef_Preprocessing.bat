@echo off
Rem This script will perform the FBRef data cleaning and preprocessing for the different seasons

Rem Directory which contains FBRef stats for the diferents seasons
set FBREF_REPOSITORY=FBRef\BIG5
Rem Directory which contains Transfermarkt player data for the diferents seasons
set TRANSFERMARKT_REPOSITORY=Transfermarkt

echo Performing FBRef data cleaning
C:\Users\Ignacieitor\anaconda3\python.exe fbref_clean.py %FBREF_REPOSITORY% %TRANSFERMARKT_REPOSITORY%

echo FBRef data cleaning done!
pause
