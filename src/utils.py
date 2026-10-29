import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

import requests
from io import StringIO
import time
import os
from pathlib import Path

from config import ROOT, BASE_URL, HTTP_HEADER

def http_get(url):
    '''
    Does a get request at the specified URL with all desired headers, changes the encoding, and sleeps so that it isnt missed on accident.
    '''
    
    req = requests.get(url, headers=HTTP_HEADER)
    req.encoding = 'utf-8'                          # these are necessary to ensure that the names get encoded correctly if they are accented
    time.sleep(3.3)                                 # need to rest or the site might get mad at us
    return req

def scrape_per_game_tables(start : int, end : int):
    '''
    start - year which the first season who's per-game data to download begins
    end - year which the last season who's per-game data to download begins
    
    Scrapes the per-game pages of basketball-reference from "start" year to "end" year.
    Because it adds a comment to the top of the csv to describe the columns you need to include a comment="#" when using pandas read_csv() function.
    '''
    for year in range(start+1,end+2):                   # the urls label the 'year' of a season by the end year whereas we chose the start year
        print(f'Scraping data for the {year-1}-{year} season...')
        dirname = f'/data/{year-1}-{year}_season'
        filename = f'per_game_stats_{year-1}-{year}.csv'
        filepath = str(ROOT) + dirname +'/' + filename
        os.makedirs(str(ROOT) + dirname, exist_ok=True)
        
        url_add = f'/leagues/NBA_{year}_per_game.html'
        req = http_get(url=BASE_URL+url_add)             
        soup = BeautifulSoup(req.text,'html.parser')
        
        df = pd.read_html(StringIO(req.text), encoding='utf-8')
        df = df[0].drop(columns=['Rk','Awards'])
        df = df.iloc[:-1]
        
        # we need to include the player code that basketball-reference puts in its individual player pages in the data so that we can distinguish players with the same name
        player_codes = [item.td['data-append-csv'] for item in soup.table.find_all('tr')[1:-1] if item.td.get('data-append-csv')]
        df.insert(0,'Code',player_codes)
        
        # we would like to also have the year, team wins and team losses as data.  Unfortuantely these are not on the per-game page
        print(f'Adding team win/losses...')
        
        url_add = f'leagues/NBA_{year}_ratings.html'
        team_req = http_get(url=BASE_URL+url_add)
        team_soup = BeautifulSoup(team_req.text, "html.parser")
        team_data = team_soup.find_all('table')[0].find_all('tr')[2:]
        
        df.insert(0,'Year',[year-1]*len(df))
        df.insert(1,'W%',[0.0]*len(df))
        for team in team_data:
            code = team.a['href'][7:10]
            wl = [int(item.get_text()) for item in team.find_all("td")[3:5]]
            df.loc[df['Team'] == code, 'W%'] = wl[0]/(wl[0]+wl[1])
        # dealing with multi-team players.  There nTM line will be a weighted average of their contributions to the win percent of the teams they played for
        for row in df.loc[df['Team'].str.endswith('TM')].itertuples():
            n_teams = int(row.Team[0])
            ind = row.Index
            gp = row.G
            tot = 0
            for offset in range(1,n_teams+1):
                tot += df.iloc[ind+offset]['W%']*df.iloc[ind+offset]['G']
            df.loc[ind,'W%'] = tot/gp
        
        # now we add a column with the MVP point share recieved by each player
        print(f'Adding MVP vote share...')
        # scrape the data and put it in a df
        url_add = f'awards/awards_{year}.html'
        mvp_req = http_get(url=BASE_URL+url_add)
        mvp_soup = BeautifulSoup(mvp_req.text, 'lxml')
        mvp_df = pd.read_html(StringIO(mvp_req.text), encoding='utf-8',header=1)[0]
        player_codes = [item.td['data-append-csv'] for item in mvp_soup.table.find_all('tr')[2:] if item.td.get('data-append-csv')]   # need the codes to match the data to our main df
        mvp_df.insert(0,'Code',player_codes)
        # add a column to the df that is to be exported and populate it
        df['MVP'] = [0.0]*len(df)
        for player_code in mvp_df.Code:
            df.loc[df['Code'] == player_code, 'MVP'] = sum(mvp_df[mvp_df['Code'] == player_code]['Share'])
        
        # export the df to a csv
        df.to_csv(filepath,encoding='utf-8',index=False)
        
        # add a comment to the top of the csv to explain the columns
        csv_comment = (
            ['Season start year','Team win percentage', 'Player ID for website URL'] 
            + [item.attrs.get('data-tip',item.get_text()) for item in soup.find_all('table')[1].find_all('tr')[0].find_all('th')[1:-1] ] 
            + ['MVP point share']
        )
        with open(filepath, 'r', encoding='utf-8') as f:
            og = f.read()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'# {",".join(csv_comment)}\n' + og)
        
def player_stat_dataframe(start: int, end: int)-> pd.DataFrame:
    '''
    start - year which the first season began
    end - year which the last season began
    
    Returns a dataframe from the csvs that are created by scrape_per_game_tables().
    '''
    
    df = pd.DataFrame()
    for d in sorted(Path(str(ROOT)+'/data').iterdir()):
        # only include years in the desired range
        if int(d.name[:4]) not in list(range(start, end+1)):
            continue
        # attach the desired data to a dataframe and return it
        for f in Path(str(ROOT)+'/data/'+d.name).iterdir():
            filepath = str(ROOT) + f'/data/{d.name}/{f.name}'
            df_tmp = pd.read_csv(filepath,encoding='utf-8',comment='#')
            df = pd.concat([df,df_tmp],ignore_index=True)
    return df