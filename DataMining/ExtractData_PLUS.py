# This script is very similar to ExtractData.py - here you can find more details about this script. 
# Here I added some addtition atributes for dataframe - which will be needed for Horse Racing Model.


import pandas as pd
import numpy as np
import re



data_file = '/Users/[...]/2022.csv'
df = pd.read_csv(data_file, sep=';', decimal=',')
df['Unnamed: 0'] = df['Unnamed: 0'].replace(np.nan, '', regex=True)

distances = []  # race distance
times = []      # race tiem
horses = []     # horses
interval = []   # distances between horses
category = []   # race category
jockeys = []    # jockeys
starters = []   # starting number
results = []    # race result
dates = []      # date
days = []       # race day number
runs = []       # race number
bloods = []     # breed

pattern_date = "\d{2}[/.]\d{2}[/.]\d{4}"
pattern_day = "\w{5} \d+"


# Extracting data from mess .csv:
for i in range(len(df)):
    pointer = df.iloc[i,0]
    if "DZIEŃ" in pointer:
        day = re.findall(pattern_day, pointer)[0]
        date = re.findall(pattern_date, pointer)[0]
    if "WYNIK GONITWY" in pointer:
        run = re.findall("\d+", re.findall("WYNIK GONITWY \d+", pointer)[0])[0]
        runs.append(run)
        days.append(day)
        dates.append(date)
    if "Gonitwa" in pointer:
        if "arabskiej" in pointer:
            bloods.append("oo")
        else:
            bloods.append("xx")
    if "KAT" in pointer:
        idx = pointer.find("KAT")
        category.append(pointer[idx + 5])
    elif "grupy" in pointer:
        idx = pointer.find("grupy")
        tmp = pointer[idx-4:idx-1].strip()
        if tmp[0].islower():
            tmp = tmp[-1]
        category.append(tmp)
    if "DYSTANS:" in pointer:
        idx = pointer.find(":")
        distances.append(int(pointer[idx+2:idx+6]))
    if pointer == "KOLEJNOŚĆ":
        j = 1
        horse = []
        jockey = []
        starter = []
        result = []
        while not (pd.isna(df.iloc[i+j,2])):
            result.append(df.iloc[i+j,0])
            horse.append(df.iloc[i+j,2])
            jockey.append(df.iloc[i+j,3])
            starter.append(df.iloc[i+j, 4])
            j+=1
        results.append(result)
        horses.append(horse)
        jockeys.append(jockey)
        starters.append(starter)
    if pointer == "Czas":
        if len(re.findall("\d\'\d+,\d", df.iloc[i,1])) > 0 :
            tmp = df.iloc[i,1][:6]
            times.append(int(tmp[0])*60 + int(tmp[2:4]))
        elif len(re.findall("\d+'\d+", df.iloc[i,1])) > 0:
            tmp = df.iloc[i,1][:4]
            times.append(int(tmp[0])*60 + int(tmp[2:4]))
        else:
            tmp = re.findall("\d+,\d", df.iloc[i,1])[0]
            times.append(int(tmp[0:2]))
    if pointer == "Odległości":
        interval.append([0] + re.split("-", df.iloc[i,1]))

# Now we can make dataframe with this data:
count = 0
for element in horses:
    count += len(element)

dane = pd.DataFrame(columns = ['Date', 'Race_Day', 'Race_idx', 'Race_NB', 'Distance', 'Category', 'Blood', 'Time', 'Result', 'Speed',
                               'Start_NB', 'Horse', 'IsFrance', 'IsIrleand', 'IsPoland', 'Title', 'Jockey', 'Weight', 'Interval', 
                               '1OG', '2OG', '3OG', '4OG', '1HG', '2HG', '3HG', '4HG', '1LG', '2LG', '3LG', '4LG', 
                               ],
                    index = range(count))

# Here is a little difference. I will add more columns from 1OG to 4LG (boolen values: 1 or 0)
# Meaning for example if horse won race Out of Group (Category A or B) then we will sign 1 (true) 
# And as well for 2., 3. and 4. place.
# OG - out group (A, B)
# HG - high group (I, II)
# LG - low group (III, IV)
# This is some preparation for Horse Racing Model.
# In addition we will add three columns from where horse came from:
# IsFrance - 1 is from France, 0 is not;
# IsIrleand - same logic;
# IsPoland - same logic;
# Other countries we can skip, are not important in my model.

k = 0
for i in range(len(horses)):
    sum_i = 0
    for j in range(len(horses[i])):
        dane['Date'][k] = dates[i]
        dane['Race_Day'][k] = days[i]
        dane['Race_idx'][k] = i
        dane['Race_NB'][k] = int(runs[i])
        dane['Distance'][k] = distances[i]
        dane['Category'][k] = category[i]
        dane['Blood'][k] = bloods[i]
        dane['Time'][k] = times[i]
        dane['Speed'][k] = dane['Distance'][k]/dane['Time'][k]
        if results[i][j] == "=":
            dane['Result'][k] = 0
        else:
            dane['Result'][k] = int(results[i][j])
        dane['Start_NB'][k] = int(starters[i][j])
        horsy = horses[i][j]
        if "(" in horsy:
            tmp = re.findall("\(\D+\)", horsy)[0]
            country = tmp[1:len(tmp)-1]
            dane['IsPoland'][k] = 0
            dane['IsFrance'][k] = 0
            dane['IsIrleand'][k] = 0
            if country == "FR":
                dane['IsFrance'][k] = 1
            elif country == "IRE":
                dane['IsIrleand'][k] = 1
            tmp = re.findall("\D+ \(", horsy)[0]
            dane['Horse'][k] = tmp[0:len(tmp)-2]
        else:
            dane['IsPoland'][k] = 1
            dane['IsFrance'][k] = 0
            dane['IsIrleand'][k] = 0
            dane['Horse'][k] = horses[i][j]
        jocky = jockeys[i][j]
        if len(re.findall('[a-ż]+\.', jocky)) > 0 :
            if "dż." in jocky: dane['Title'][k] = 1
            elif "k. dż." in jocky: dane['Title'][k] = 2
            elif "pr. dż." in jocky: dane['Title'][k] = 3
            elif "st. u." in jocky: dane['Title'][k] = 4
            elif "u." in jocky: dane['Title'][k] = 5
            else: print("Other case Jockey Level at: ", i)
        else:
            if "(-1)" in jocky: dane['Title'][k] = 2
            elif "(-2)" in jocky: dane['Title'][k] = 3
            elif "(-3)" in jocky: dane['Title'][k] = 4
            elif "(-4)" in jocky: dane['Title'][k] = 5
            else: print("Other case Jockey Level at: ", i)
        if len(re.findall(" [A-Ż]\.\S{3,40} ", jocky)) > 0 :
            dane['Jockey'][k] = re.findall(" [A-Ż]\.\S{3,40} ", jocky)[0].strip()
        else :
            dane['Jockey'][k] = re.findall("[A-Ż]\.[A-Ża-ż]\. [A-Ża-ż]+", jocky)[0]
        dane['Weight'][k] = float(re.findall("\d+\.\d", jocky)[0])
        if results[i][j] == "=" :
            dane['Interval'][k] = np.NAN
        else :
            inter = interval[i][j]
            if isinstance(inter, int):
                sum_i += float(inter)
            elif inter.isnumeric():
                sum_i += float(inter)
            elif len(inter) == 1 :
                if 'Ѕ' in inter:
                    sum_i += 0.5
                elif 'ѕ' in inter:
                    sum_i += 0.75
                elif 'ј' in inter:
                    sum_i += 0.25
                else:
                    print(i,'',j)
                    print(inter)
                    print("inny przypadek len=1")
            elif len(inter) == 2:
                if 'Ѕ' in inter:
                    sum_i += float(inter[0]) + 0.5
                elif 'ѕ' in inter:
                    sum_i += float(inter[0]) + 0.75
                elif 'ј' in inter:
                    sum_i += float(inter[0]) + 0.25
                else:
                    print(i,'',j)
                    print(inter)
                    print("inny przypadek len=2")
            else:
                if inter == 'szyja' :
                    sum_i += 0.3
                elif inter == 'nos' :
                    sum_i += 0.05
                elif inter == 'kr. łeb' :
                    sum_i += 0.1
                elif inter == 'łeb' :
                    sum_i += 0.2
                elif inter == 'łeb w łeb' :
                    sum_i += 0
                elif 'daleko' in inter :
                    sum_i += float(re.findall("\d+", inter)[0])
                else:
                    print(i,'',j)
                    print(inter)
                    print("inny przypadek len>2")
            dane['Interval'][k] = sum_i
        # Check the place and category for race:
        if category[i] in ['A', 'B']:
            if results[i][j] == '1':
                dane['1OG'][k] = 1
            elif results[i][j] == '2':
                dane['2OG'][k] = 1
            elif results[i][j] == '3':
                dane['3OG'][k] = 1
            elif results[i][j] == '4':
                dane['4OG'][k] = 1
        elif category[i] in ['I', 'II']:
            if results[i][j] == '1':
                dane['1HG'][k] = 1
            elif results[i][j] == '2':
                dane['2HG'][k] = 1
            elif results[i][j] == '3':
                dane['3HG'][k] = 1
            elif results[i][j] == '4':
                dane['4HG'][k] = 1
        elif category[i] in ['III', 'IV']:
            if results[i][j] == '1':
                dane['1LG'][k] = 1
            elif results[i][j] == '2':
                dane['2LG'][k] = 1
            elif results[i][j] == '3':
                dane['3LG'][k] = 1
            elif results[i][j] == '4':
                dane['4LG'][k] = 1
        k+=1
 


dane['1OG'] = dane['1OG'].replace(np.nan, 0, regex=True)
dane['2OG'] = dane['2OG'].replace(np.nan, 0, regex=True)
dane['3OG'] = dane['3OG'].replace(np.nan, 0, regex=True)
dane['4OG'] = dane['4OG'].replace(np.nan, 0, regex=True)

dane['1HG'] = dane['1HG'].replace(np.nan, 0, regex=True)
dane['2HG'] = dane['2HG'].replace(np.nan, 0, regex=True)
dane['3HG'] = dane['3HG'].replace(np.nan, 0, regex=True)
dane['4HG'] = dane['4HG'].replace(np.nan, 0, regex=True)

dane['1LG'] = dane['1LG'].replace(np.nan, 0, regex=True)
dane['2LG'] = dane['2LG'].replace(np.nan, 0, regex=True)
dane['3LG'] = dane['3LG'].replace(np.nan, 0, regex=True)
dane['4LG'] = dane['4LG'].replace(np.nan, 0, regex=True)


#'1OG', '2OG', '3OG', '4OG', '1HG', '2HG', '3HG', '4HG', '1LG', '2LG', '3LG', '4LG'

dane.to_csv('2022_czyste.csv')
