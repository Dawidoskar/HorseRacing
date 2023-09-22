# Purpose of this script is to transform mess data from webpage to clean data set from whole racing season on Tor Służewiec (Warsaw, Poland).
# Data were copied from: https://torsluzewiec.pl/dzien-wyscigowy/dzien-1-2023/ to table and then export as .csv file.
# But I omit race for French trotters and jumping races.
# Unfortunately, because of web structure it was impossible to extract this data with BeautifulSoup from html - at least for now for me it is to difficult. 


# Import necessary libraries:
import pandas as pd
import numpy as np
import re


# Read source data:
data_file = '[...]/2022.csv' 
df = pd.read_csv(data_file, sep=';', decimal=',')

# To avoid errors caused by NULL values, I will replace NULL in first column with blank text:
df['Unnamed: 0'] = df['Unnamed: 0'].replace(np.nan, '', regex=True)

# Here are some list which will be needed to store data during this step:
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

# Few times I will use also Regular Expression to distinguish some specific data.
# Here are two pattern to extract date and number of racing day from string like: 
# "DZIEŃ 1 - 24.04.2022"
pattern_date = "\d{2}[/.]\d{2}[/.]\d{4}" # will extract 24.04.2022
pattern_day = "\w{5} \d+" # will extract "DZIEŃ 1"


# Extracting data from mess .csv:
for i in range(len(df)):
    pointer = df.iloc[i,0]
# If we will find in first column string contain "DZIEŃ" (DAY) then we will extract Date and Racing Day from this string.
# For now it will be stored in two variables "day" and "date".
    if "DZIEŃ" in pointer:
        day = re.findall(pattern_day, pointer)[0]
        date = re.findall(pattern_date, pointer)[0]
# Here we will extract race number from string like "WYNIK GONITWY 1 - NAGRODA DANDOLO – HANDIKAP OTWARCIA"
# We are intresting only in numer "Result Race 1 - [...]"
    if "WYNIK GONITWY" in pointer:
        run = re.findall("\d+", re.findall("WYNIK GONITWY \d+", pointer)[0])[0]
# Here we are appending three list:
# runs - with run number (in a racing day)
# days, dates - as well here to store this same number of "days" and "dates" as "runs"
# it will make life easer during next phase (with creating new dataframe)
        runs.append(run)
        days.append(day)
        dates.append(date)
# From race description I will take the horse breed.
# If the race is for arabian horses then there will be word "arabskiej" 
# in other case we have thoroughbred horses.
# Example descrpiton:
# "Gonitwa handikapowa I grupy dla 4-letnich i starszych koni. Wagi według handikapu generalnego minus 14 kg."
    if "Gonitwa" in pointer:
        if "arabskiej" in pointer:
            bloods.append("oo")
        else:
            bloods.append("xx")
# From this same description we can check which category had this race: I, II, III, IV
# But we also have highest categories like: A, B - which we can find only in race name:
# "WYNIK GONITWY 5 - NAGRODA STRZEGOMIA (SPECJALNA) – (KAT. B)"
# For A, B we are looking in race name for word "KAT" (Category),
# and for I, II, III, IV we are looking for grupy (group). 
    if "KAT" in pointer:
        idx = pointer.find("KAT")
        category.append(pointer[idx + 5])
    elif "grupy" in pointer:
        idx = pointer.find("grupy")
        tmp = pointer[idx-4:idx-1].strip()
        if tmp[0].islower():
            tmp = tmp[-1]
        category.append(tmp)
# There we are saving race distance from: "DYSTANS: 1600"
    if "DYSTANS:" in pointer:
        idx = pointer.find(":")
        distances.append(int(pointer[idx+2:idx+6]))
# Next field is "KOLEJNOŚĆ" - results order from racing.
# Horses names, jockey names and starting number are in different columns. 
# For each race we will create a list of this attributes and save in "main" list.
# Each result has his own "row" so we need a small loop inside:
    if pointer == "KOLEJNOŚĆ":
        j = 1
        horse = []
        jockey = []
        starter = []
        result = []
# Between "result" other cells are filled with NULL values.
# We don't know how many horses paricipeted in race, but we can create
# while loop catching null values - after last horse we are expecting 
# null value in cell. 
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
# After result, we are expecting "CZAS" - time, race time attribut.
# For my use, I will convert time to seconds and only time for whole race.
# I will not focus on intermediate times (in brackets)
# Example: "1'40,7" (8,3-29,3-31,2-31,9)" -> 1 min 40 seconds -> 100 seconds. 
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
# And the last attribut is distances between horses:
# "Ѕ-kr. łeb-3Ѕ-5Ѕ-łeb-Ѕ-2-16"
# Where - because of coping it from website: 
# 1/4 was saved as j
# 1/2 was saved as S
# 3/4 was saved as s
# We are spliting this distances - and add first "distance" equal to 0 
# (first horse was 0 distances after first horse ;) )
    if pointer == "Odległości":
        interval.append([0] + re.split("-", df.iloc[i,1]))

# Now we can make dataframe with this data:
# First we have to count how many space for our data we need:
count = 0
for element in horses:
    count += len(element)

# Now we will create an empty DataFrame:
dane = pd.DataFrame(columns = ['Date', 'Race_Day', 'Race_idx', 'Race_NB', 'Distance', 'Category', 'Blood', 'Time', 'Result', 'Speed',
                               'Start_NB', 'Horse', 'Country', 'Title', 'Jockey', 'Weight', 'Interval'],
                    index = range(count))

# And here we are to fill all cells with data saved in lists from firs loop:
k = 0
# Here we are going throuht all elements from lists,
# but remember that we have also list inside list that's why we
# need another loop inside. 
# We can imagine this like first loop (i) is going through races 
# and second loop (j) is going through horses participating in race "i". 
for i in range(len(horses)):
    sum_i = 0 #this will sum intervals / distances after first horse - after each race it has to be set to 0. 
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
        # We will get some result equal to = <- that means that horse was not participating in race
        # I decided in this case to save it as "0". 
        if results[i][j] == "=":
            dane['Result'][k] = 0
        else:
            dane['Result'][k] = int(results[i][j])
        dane['Start_NB'][k] = int(starters[i][j])
        # Here we are taking a country from which horse is from string like:
        # "Kaneshya (FR)" -> means horse is from France
        # Polish horses don't have country prefix after name: "Dakini"
        horsy = horses[i][j]
        if "(" in horsy:
            tmp = re.findall("\(\D+\)", horsy)[0]
            dane['Country'][k] = tmp[1:len(tmp)-1]
            tmp = re.findall("\D+ \(", horsy)[0]
            dane['Horse'][k] = tmp[0:len(tmp)-2]
        else:
            dane['Country'][k] = "PL"
            dane['Horse'][k] = horses[i][j]
        # With Jockey name we will also get information about jockey level
        # In Poland we have:                     Dżokej,  Kandydat Dżokejski, Praktykant Dżokejski, Starszy Uczeń, Uczeń
        # And that means how many races Jockey won: >100, [50, 100),          [25, 50),              [10, 25)      , <10
        # And how much weight was the horse carrying.
        # Example: "dż. A.Sxxxxxxx (59.0)"
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
      # And at the end we are checking the distance after first horse for other horses:
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
                # Just in case if some other date will be saved as strange sign, 
                # and there will be a need to add more cases in the future. 
                    print(i,'',j)
                    print(inter)
                    print("Other case len=1")
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
                    print("Other case len=2")
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
                    print("Other case len>2")
            dane['Interval'][k] = sum_i
        k+=1


# And at the end we can save our dataframe to .csv file!
dane.to_csv('2022_clean.csv')
