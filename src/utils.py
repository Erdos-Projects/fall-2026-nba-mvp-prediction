import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

import requests
from io import StringIO
import time
import os

from config import ROOT, BASE_URL, HTTP_HEADER

def scrape_per_game_tables(start : int, end : int):
    '''
    start - year which the first season who's per-game data to download begins
    end - year which the last season who's per-game data to download begins
    
    Scrapes the per-game pages of basketball-reference from "start" year to "end" year.
    Because it adds a comment to the top of the csv to describe the columns you need to include a comment="#" when using pandas read_csv() function.
    '''
    for year in range(start+1,end+2):                   # the urls label the 'year' of a season by the end year whereas we chose the start year
        print(f'Scraping data for the {year-1}-{year} season...')
        url_add = f'/leagues/NBA_{year}_per_game.html'
        dirname = f'/data/{year-1}-{year}_season'
        filename = f'per_game_stats_{year-1}-{year}.csv'
        filepath = str(ROOT) + dirname +'/' + filename
        os.makedirs(str(ROOT) + dirname, exist_ok=True)
        
        req = requests.get(url=BASE_URL+url_add,headers=HTTP_HEADER)
        soup = BeautifulSoup(req.text,'html.parser')
        
        df = pd.read_html(StringIO(req.text), encoding='utf-8')
        df = df[0].drop(columns=['Rk','Awards'])
        df = df.iloc[:-1]
        
        
        # we would like to also have the year, team wins and team losses as data.  Unfortuantely these are not on the per-game page
        df.insert(0,'Year',[year-1]*len(df))
        df.insert(1,'Wins',[0]*len(df))
        df.insert(2,'Losses',[0]*len(df))
        print(f'Adding team win/losses...')
        time.sleep(3.3)
        team_req = requests.get(url=(BASE_URL+f'leagues/NBA_{year}_ratings.html'), headers=HTTP_HEADER)
        team_soup = BeautifulSoup(team_req.text, "html.parser")
        team_data = team_soup.find_all('table')[0].find_all('tr')[2:]
        for team in team_data:
            code = team.a['href'][7:10]
            df.loc[df['Team'] == code, ['Wins','Losses']] = [int(item.get_text()) for item in team.find_all("td")[3:5]]
        df.loc[df['Team'].str.endswith('TM'),['Wins','Losses']] = np.nan
        
        df.to_csv(filepath,encoding='utf-8',index=False)
        
        # add a comment to the top of the csv to explain the columns
        csv_comment = ['Season start year','Team wins', 'Team losses'] + [item.attrs.get('data-tip',item.get_text()) for item in soup.find_all('table')[1].find_all('tr')[0].find_all('th')[1:-1] ]
        with open(filepath, 'r', encoding='utf-8') as f:
            og = f.read()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'# {",".join(csv_comment)}\n' + og)
        
        time.sleep(3.3)                                 # need to rest or the site might get mad at us