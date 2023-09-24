# Hi!
# This script was made for data delivered from https://koniewyscigowe.pl
# There are data from polish horse racing from 2014 till 2019 -> 26920 rows & 91 columns of data.
# Unfortunately columns names are in Polish, but I will try to translate to most important one. 
# This data was used to build my model.
# Have fun!
# Dawid

#Importing pandas library to manage with DataFrame
import pandas as pd
import numpy as np
import re

#Loading data from user repository: 
data_file = '/Users/dawid/Documents/PythonModel/Old/dane.csv'
df_mess = pd.read_csv(data_file)

#We don't need to keep all columns, to avoid mess we will keep only this:
columns_to_keep = ['id_wyscigu', 'data', 'id_konia', 'id_dzokeja', 'id_trenera', 'miejsce_konia', 
                   'nr_startowy', 'waga', 'wygrana', 'odleglosc', 'tytul_dzokeja', 
                   'nazwa','dystans','kategoria','czas', 'rasa',
                   'stan_toru','nazwa.3', 'plec','panstwo','nr_dnia_wysc', 'nr_w_dniu', 'miasto', 'data_ur']

# This information we will need for next steps:
# rasa == Breed, we are intresing in values:
# 	0 :: Pure Arab Blood (oo)
# 	1 :: Thoroughbred (xx)
# typ_wyscigu == Race Type:
#	1 - "flat" racing (normal)
#	2, 3, 4 - we are not intrested in this races (some jumping etc) 
# And we will keep only some columns:
# 	id_wyscigu == race_id
# 	data == date
#	id_konia == horse_id
#	id_dzokeja == jockey_id
#	id_trenera == trainer_id
#	miejsce_konia == result
#	nr_startowy == start number
#	waga == jockey weight
#	wygrana == prize
#	odleglosc == distance after previous horse
#	tytul_dzokeja == jockey level
#	nazwa == race name
#	dystans == distance
#	kategoria == race category
#	czas == time
#	rasa == breed
#	stan_toru == track condition
#	nazwa.3 == horse name
#	plec == horse gender 
#	panstwo == horse origin
#	nr_dnia_wysc == number of race day
#	nr_w_dniu == number of the race
#	miasto == city (in Poland: Warsaw, Wroclaw or Sopot - three race tracks;
#	data_ur == Date of birth for horse

race_all = df_mess[(df_mess['typ_wyscigu']==1) & ((df_mess['rasa']==0) | (df_mess['rasa']==1))][columns_to_keep]

# Data management 
# Here we will extract Season == Year from the date:
race_all['Season'] = race_all['data'].apply(lambda x: pd.to_datetime(x).year)
race_all.drop(columns=['data'], inplace=True)

# Filling missing values**
#	** as you can see I checked already my data, so I know what we need to replace etc. 
#		but in that case, I will not explain this process.
# 	It's because there were some mistakes in DB.  
race_all.loc[race_all['id_wyscigu'].isin([218, 13953, 13973, 14021, 14042, 14461, 14516, 14525, 14638, 14736,
                                    15077, 15082, 15123, 15159, 15201, 15256, 15735, 15742, 15788, 15852, 15890,
                                    15956, 16285, 16310, 16319, 16348, 16370, 16438, 16441]),'kategoria']="II"
race_all.loc[race_all['id_wyscigu'].isin([14436, 14438, 14536, 14856, 14629, 14569, 15062, 
                                                  15064, 16416, 16633]),'kategoria']="III"
race_all.loc[race_all['id_wyscigu'].isin([14442, 14520]),'kategoria']="IV"

# Wrong type of race... 
race_all.drop(race_all[race_all.id_wyscigu == 15070].index, inplace=True)

# Reset index in df:
race_all.reset_index(inplace=True)
race_all.drop(columns=['index'], inplace=True)
race_all['czas'].fillna('1\'40', inplace=True)


# Here we will count the horse age (season == year of race - year from date of birth) - later:
race_all['Age'] = 0

# First operation:
#	- Distance_af_first (Distance after first horse)
#	- Speed (speed of the race counting from distance and time of race*)
# 		* of course that only mean that avarage speed for horse which was first was XXX
#			for rest horses it will be a little different. 
race_prev = 1
dist = 0
race_all['Distance_af_first'] = np.nan
race_all['Speed'] = np.nan
sped = race_all['dystans'][0]/(int(race_all['czas'][0][0])*60+int(race_all['czas'][0][2:4]))
# Here we will take the first race (race_id == 1) 
# Race_id is from database so it is unique for every race (regardless of the year)
tmp = race_all[race_all['id_wyscigu'] == 1]
maxb = max(tmp['waga'])
race_all['Balance'] = np.nan

# First loop to perform some calculations:
for i in range(len(race_all)):
    race_all.loc[i, 'Age'] = race_all.loc[i, 'Season']-int(race_all.loc[i, 'data_ur'][0:4])
    race_id = race_all.loc[i, 'id_wyscigu']
    # We are checking if we are counting values still for this same race:
    if race_id == race_prev :
        dist = dist + race_all.loc[i, 'odleglosc']
        race_all.loc[i, 'Distance_af_first'] = dist
        race_all.loc[i, 'Speed'] = sped
        race_all.loc[i, 'Balance'] = race_all.loc[i, 'waga'] - maxb
    # If we switch the race to the new one, then we need to change some variables etc.:
    else :
        dist = 0
        race_all.loc[i, 'Distance_af_first'] = dist
        if re.search('^\d{2}', race_all['czas'][i]):
            sped = race_all.loc[i, 'dystans']/(int(race_all.loc[i, 'czas'][0:2]))
        else:
            sped = race_all.loc[i, 'dystans']/(int(race_all.loc[i, 'czas'][0])*60+int(race_all.loc[i, 'czas'][2:4]))
        race_prev = race_id
        race_all.loc[i, 'Speed'] = sped
        tmp = race_all[race_all['id_wyscigu'] == race_id]
        maxb = max(tmp['waga'])
        race_all.loc[i, 'Balance'] = race_all.loc[i, 'waga'] - maxb

# Here we are adding new columns where we are checking from which country is our horse.
# From some other analysis I know that for us only France, Ireland and Poland are important. 
race_all['IsFrance'] = np.where(race_all['panstwo']==74,1,0)
race_all['IsIreland'] = np.where(race_all['panstwo']==105,1,0)
race_all['IsPoland'] = np.where(race_all['panstwo']==176,1,0)

# We can also remove some columns that we don't need anymore:
race_all.drop(columns=['panstwo'], inplace=True)
race_all.drop(columns=['czas'], inplace=True)
race_all.drop(columns=['odleglosc'], inplace=True)
race_all.drop(columns=['waga'], inplace=True)
race_all.drop(columns=['data_ur'], inplace=True)

# And rename the rest of them:
race_all.rename(columns={"id_wyscigu":"Race_ID",
                             "id_konia":"Horse_ID",
                             "id_dzokeja":"Jockey_ID",
                             "id_trenera":"Trainer_ID",
                             "miejsce_konia":"Result",
                             "nr_startowy":"Start_NB",
                             "wygrana":"Price",
                             "tytul_dzokeja":"Jockey_LVL",
                             "nazwa":"Race_Name",
                             "dystans":"Distance",
                             "kategoria":"Category",
                             "stan_toru":"Track_Cond",
                             "nazwa.3":"Horse_Name",
                             "plec":"Gender",
                             "nr_dnia_wysc":"Race_Day",
                             "nr_w_dniu":"Race_NB",
                             "miasto":"City"}, inplace=True)

# Here we will add some boolean value for horse gender:
# o - stallion, w - gelding -> 1, and other case mare -> 0
race_all['Gender'] = np.where((race_all['Gender']=='o') | (race_all['Gender']=='w'),1,0)

# More counting! 
#	Avg_DAF -> Avarage Distance After First Horse - for a horse from races that he participated so far;
#	Avg_Speed -> Avarage Speed;
#	First, Sec... -> counting how many times so far horse was 1., 2., 3. or 4. in
#		> all races 
#		> LowGroup -> Category: III, IV
#		> HighGroup -> Category: I, II
#		> OutGroup -> Category: A, B
#	Avg_Price -> Avarage Prize;
#	Avg_Distance -> Avarage Distance;
race_all['Avg_DAF'] = 0
race_all['Avg_Speed'] = 0
race_all['First'] = 0
race_all['Second'] = 0
race_all['Third'] = 0
race_all['Fourth'] = 0

race_all['First_LowGroup'] = 0
race_all['Second_LowGroup'] = 0
race_all['Third_LowGroup'] = 0
race_all['Fourth_LowGroup'] = 0

race_all['First_HighGroup'] = 0
race_all['Second_HighGroup'] = 0
race_all['Third_HighGroup'] = 0
race_all['Fourth_HighGroup'] = 0 

race_all['First_OutGroup'] = 0
race_all['Second_OutGroup'] = 0
race_all['Third_OutGroup'] = 0
race_all['Fourth_OutGroup'] = 0

race_all['Avg_Price'] = 0
race_all['Avg_Distance'] = 0

# Here some timing, to check how much time it will take; for me it's around 2 minutes and 20 sec. 
import time
from datetime import timedelta

tmp_count = 0
start_time = time.monotonic()
for i in range(len(race_all)):
    if i == 0:
        continue
    h_id = race_all.loc[i, 'Horse_ID']
    sum_dis = 0
    sum_speed = 0
    counter_pl_all = [0, 0, 0, 0]
    counter_pl_lg = [0, 0, 0, 0]
    counter_pl_hg = [0, 0, 0, 0]
    counter_pl_og = [0, 0, 0, 0]
    # There are two loop, with the second loop we will check the last values of some attributes for horse;
    for j in reversed(range(i)):
        if h_id == race_all.loc[j, 'Horse_ID'] :
            if race_all.loc[j, 'Avg_Distance'] == 0 :
                race_all.loc[i, 'Avg_Distance'] = race_all.loc[j, 'Distance']
            else :
                race_all.loc[i, 'Avg_Distance'] = (race_all.loc[j, 'Avg_Distance'] + race_all.loc[j, 'Distance'])/2
            if race_all.loc[j, 'Avg_Price'] == 0 :
                race_all.loc[i, 'Avg_Price'] = race_all.loc[j, 'Price']
            else :
                race_all.loc[i, 'Avg_Price'] = (race_all.loc[j, 'Avg_Price'] + race_all.loc[j, 'Price'])/2
            sum_dis = sum_dis + race_all.loc[j, 'Distance_af_first']
            sum_speed = sum_speed + race_all.loc[j, 'Speed']
            race_all.loc[i, 'Avg_DAF'] = sum_dis / 2
            race_all.loc[i, 'Avg_Speed'] = sum_speed / 2
            counter_pl_all[0] = race_all.loc[j, 'First']
            counter_pl_all[1] = race_all.loc[j, 'Second']
            counter_pl_all[2] = race_all.loc[j, 'Third']
            counter_pl_all[3] = race_all.loc[j, 'Fourth']
            counter_pl_lg[0] = race_all.loc[j, 'First_LowGroup']
            counter_pl_lg[1] = race_all.loc[j, 'Second_LowGroup']
            counter_pl_lg[2] = race_all.loc[j, 'Third_LowGroup']
            counter_pl_lg[3] = race_all.loc[j, 'Fourth_LowGroup']
            counter_pl_hg[0] = race_all.loc[j, 'First_HighGroup']
            counter_pl_hg[1] = race_all.loc[j, 'Second_HighGroup']
            counter_pl_hg[2] = race_all.loc[j, 'Third_HighGroup']
            counter_pl_hg[3] = race_all.loc[j, 'Fourth_HighGroup']
            counter_pl_og[0] = race_all.loc[j, 'First_OutGroup']
            counter_pl_og[1] = race_all.loc[j, 'Second_OutGroup']
            counter_pl_og[2] = race_all.loc[j, 'Third_OutGroup']
            counter_pl_og[3] = race_all.loc[j, 'Fourth_OutGroup']
            if race_all.loc[j, 'Result'] == 1 :
                counter_pl_all[0] = counter_pl_all[0] + 1
                if (race_all.loc[j, 'Category'] == 'IV') or (race_all.loc[j, 'Category'] == 'III') :
                    counter_pl_lg[0] = counter_pl_lg[0] + 1
                elif (race_all.loc[j, 'Category'] == 'II') or (race_all.loc[j, 'Category'] == 'I') :
                    counter_pl_hg[0] = counter_pl_hg[0] + 1
                else :
                    counter_pl_og[0] = counter_pl_og[0] + 1
            if race_all.loc[j, 'Result'] == 2 :
                counter_pl_all[1] = counter_pl_all[1] + 1
                if (race_all.loc[j, 'Category'] == 'IV') or (race_all.loc[j, 'Category'] == 'III') :
                    counter_pl_lg[1] = counter_pl_lg[1] + 1
                elif (race_all.loc[j, 'Category'] == 'II') or (race_all.loc[j, 'Category'] == 'I') :
                    counter_pl_hg[1] = counter_pl_hg[1] + 1
                else :
                    counter_pl_og[1] = counter_pl_og[1] + 1
            if race_all.loc[j, 'Result'] == 3 :
                counter_pl_all[2] = counter_pl_all[2] + 1
                if (race_all.loc[j, 'Category'] == 'IV') or (race_all.loc[j, 'Category'] == 'III') :
                    counter_pl_lg[2] = counter_pl_lg[2] + 1
                elif (race_all.loc[j, 'Category'] == 'II') or (race_all.loc[j, 'Category'] == 'I') :
                    counter_pl_hg[2] = counter_pl_hg[2] + 1
                else :
                    counter_pl_og[2] = counter_pl_og[2] + 1
            if race_all.loc[j, 'Result'] == 4:
                counter_pl_all[3] = counter_pl_all[3] + 1
                if (race_all.loc[j, 'Category'] == 'IV') or (race_all.loc[j, 'Category'] == 'III') :
                    counter_pl_lg[3] = counter_pl_lg[3] + 1
                elif (race_all.loc[j, 'Category'] == 'II') or (race_all.loc[j, 'Category'] == 'I') :
                    counter_pl_hg[3] = counter_pl_hg[3] + 1
                else :
                    counter_pl_og[3] = counter_pl_og[3] + 1
            race_all.loc[i, 'First'] = counter_pl_all[0]
            race_all.loc[i, 'Second'] = counter_pl_all[1]
            race_all.loc[i, 'Third'] = counter_pl_all[2]
            race_all.loc[i, 'Fourth'] = counter_pl_all[3]
            race_all.loc[i, 'First_LowGroup'] = counter_pl_lg[0]
            race_all.loc[i, 'Second_LowGroup'] = counter_pl_lg[1]
            race_all.loc[i, 'Third_LowGroup'] = counter_pl_lg[2]
            race_all.loc[i, 'Fourth_LowGroup'] = counter_pl_lg[3]
            race_all.loc[i, 'First_HighGroup'] = counter_pl_hg[0]
            race_all.loc[i, 'Second_HighGroup'] = counter_pl_hg[1]
            race_all.loc[i, 'Third_HighGroup'] = counter_pl_hg[2]
            race_all.loc[i, 'Fourth_HighGroup'] = counter_pl_hg[3]
            race_all.loc[i, 'First_OutGroup'] = counter_pl_og[0]
            race_all.loc[i, 'Second_OutGroup'] = counter_pl_og[1]
            race_all.loc[i, 'Third_OutGroup'] = counter_pl_og[2]
            race_all.loc[i, 'Fourth_OutGroup'] = counter_pl_og[3]
            break
    tmp_count = tmp_count + 1
    # And some code to show progress; 
    if tmp_count == 1000:
        tmp_proc = (i*100)/len(race_all)
        tmp_proc = "{:.0f}".format(tmp_proc)
        print(tmp_proc + "%")
        tmp_count = 0

end_time = time.monotonic()
print(timedelta(seconds=end_time - start_time))

# And here counting some statistics for Traniners and Jockeys:
# How many times they won in relation to all starts (% of wins)

race_all['Jockey%'] = 0
race_all['Trainer%'] = 0

# This time it's faster, because %wins is for us important only in a specific season;
# Effeciveness of Trainer or Jockey during the season; -> around 30 sec.

tmp_count = 0
start_time = time.monotonic()
for i in range(len(race_all)):
    if i == 0:
        race_id_old = race_all.loc[i, 'Race_ID']
        i_stop = i
        continue
    race_id = race_all.loc[i, 'Race_ID']
    train_id = race_all.loc[i, 'Trainer_ID']
    jock_id = race_all.loc[i, 'Jockey_ID']
    seas = race_all.loc[i, 'Season']
    if race_id_old != race_id :
        i_stop = i
        race_id_old = race_id
    first = len(race_all[(race_all['Trainer_ID']==train_id) & (race_all['Season']==seas) & (race_all['Result']==1)].loc[:i_stop-1, 'Result'])
    rest = len(race_all[(race_all['Trainer_ID']==train_id) & (race_all['Season']==seas)].loc[:i_stop-1, 'Result'])
    if first == 0 :
        scope = 0
    else :
        scope = first/rest
    race_all.loc[i, 'Trainer%'] = scope
    first = len(race_all[(race_all['Jockey_ID']==train_id) & (race_all['Season']==seas) & (race_all['Result']==1)].loc[:i_stop-1, 'Result'])
    rest = len(race_all[(race_all['Jockey_ID']==train_id) & (race_all['Season']==seas)].loc[:i_stop-1, 'Result'])
    if first == 0 :
        scope = 0
    else :
        scope = first/rest
    race_all.loc[i, 'Jockey%'] = scope
    tmp_count = tmp_count + 1
    if tmp_count == 1000:
        tmp_proc = (i*100)/len(race_all)
        tmp_proc = "{:.0f}".format(tmp_proc)
        print(tmp_proc + "%")
        tmp_count = 0

end_time = time.monotonic()
print(timedelta(seconds=end_time - start_time))

# Add the end we will add some flag 1 when horse won, and 0 in other case.
race_all['Win'] = np.where(race_all['Result']==1,1,0)

# And delete columns that we don't need:
race_all.drop(columns=['Distance_af_first'], inplace=True)
race_all.drop(columns=['Speed'], inplace=True)


# And to now we can save it - this file will be available to download (now or later) on github.
race_all.to_csv('raceall.csv')
