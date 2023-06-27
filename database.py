# Authors: Marcel Gunadi, Trien Bang Huynh and Minh Duc Vo
import json
import numpy as np
import pandas as pd
import sqlite3
import re
import unicodedata
import requests
from bs4 import BeautifulSoup
import os

def makeDatabase(dbName = "lab.db"):
  # check if database exist
  if os.path.isfile(os.path.join(os.getcwd(), dbName)):
    return
  
  print("Loading data for:")

  data_names = ['Year', 'Rank', 'Company', 'Revenue', 'Profit']

  db = sqlite3.connect(dbName)
  cur = db.cursor()

  cur.execute(f'''DROP TABLE IF EXISTS {data_names[2]}''')
  # l[2] = company
  cur.execute(f'''CREATE TABLE {data_names[2]}(
                      id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                      {data_names[2]} TEXT UNIQUE ON CONFLICT IGNORE)''')
  cur.execute("DROP TABLE IF EXISTS Lab")
  cur.execute(f'''CREATE TABLE Lab(
                      id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                      {data_names[0]} INTEGER,
                      {data_names[1]} INTEGER,
                      {data_names[2]} INTEGER,
                      {data_names[3]} REAL,
                      {data_names[4]} REAL)''')



  corporate_suffixes = ['corporation', 'corp.', 'corp', 'incorporated', 'inc.', 'inc', 'company', 'companies', 'co.', 'co', 'limited', 'ltd.', 'ltd', 'limited liability company', 'llc', 'l.l.c.', 'l.l.c', 'group', 'groups', 'holding', 'holdings', 'technologies', 'l.p.', 'partners', 'lp', 'hldgs', 'hldg', 'hldg.', 'hldgs.', 'worldwide', 'cos', 'and', 'equity', 'financial', 'nbd', 'systems', 'energy', 'life insurance']
  names_dict = {}

  def is_abbreviation_word(str1, str2):
      if len(str1.replace('.','')) <= len(str2.replace('.','')):
          short_str = str1.replace('.','')
          long_str = str2.replace('.','')
      else:
          short_str = str2.replace('.','')
          long_str = str1.replace('.','')
      i = 0
      for char in long_str:
          # print(i, len(short_str), short_str[i], char)
          if i < len(short_str) and short_str[i] == char:
              i += 1

      return i == len(short_str) and str1[0] == str2[0]

  def is_abbreviation_string(str1, str2):
      if len(str1.replace('.','')) <= len(str2.replace('.','')):
          short_str = str1.replace('.','').split()
          long_str = str2.replace('.','').split()
          # check_string = True
      else:
          short_str = str2.replace('.','').split()
          long_str = str1.replace('.','').split()
      i = 0
      for word in long_str:
          if i < len(short_str) and is_abbreviation_word(word, short_str[i]):
              i += 1
          # print(i, len(short_str), word, short_str[i], is_abbreviation_word(word, short_str[i]))
      return (i == len(short_str) and len(short_str) > 1) or str1 == str2#, short_str == str1.replace('.','').split()

  def remove_suffix(names):

      # Standardizing lettercase
      names = names.lower()

      # Standardizing punctuation
      names = re.sub(r',([^\s])', r', \1', names)

      # Standardizing whitespace
      names = re.sub(r'\s+', ' ', names)

      # Standardizing accented and special characters
      names = unicodedata.normalize('NFKD', names).encode('ascii', 'ignore').decode('ascii')

      words = names.strip().split(',')[0].split('(')[0].split()
      if words[0] == "the":
          words.pop(0)
      while words[-1] in corporate_suffixes:
          words.pop()
      new_name = " ".join(words)
      new_name = new_name.replace('&', 'and')
      for names_s in names_dict.keys():
        if is_abbreviation_string(names_s, new_name):
          names_dict[names_s].append(new_name)
          return names_s
      names_dict[new_name] = [new_name]
      return new_name


  links = [['1', '101', '201', '301', '401'], ['index', '101_200', '201_300', '301_400', '401_500']] # For all splits of rank
  links_num = 0
  l = [0, 0, 0, 0, 0]
  num = []
  wrong_cnt = 0
  data_df = pd.DataFrame(columns = data_names)
  for year in range(1955, 2013): # 1955 - 2012
    cnt = 0
    web_df = pd.DataFrame(columns = data_names)
    wrong = []
    l[0] = year # populate l with years
  
    for link in links[l[0] > 2005]:

      if l[0] <= 2005:
        links_str = f'https://money.cnn.com/magazines/fortune/fortune500_archive/full/{year}/{link}.html'
      else:
        links_str = f'https://money.cnn.com/magazines/fortune/fortune500/{year}/full_list/{link}.html'
      page = requests.get(links_str)

      soup = BeautifulSoup(page.content, "lxml")
      if l[0] == 2007:
        start = 8
        end = 107
      elif l[0] == 2008:
        start = 14
        end = 113
      elif l[0] >= 2009:
        start = 2
        end = 101
      else:
        start = 6
        end = 105
      for ind, i in enumerate(soup.select('table tr'  )):#, href=True): # gets all the tr tags

        if end >= ind >= start:
          cnt+=1 # Increment num for each company
          for id, j in enumerate(i.select('td')): # go over all td tags

            try:
              if id == 0:  # rank
                l[id + 1] = int(j.text.strip())
              elif id == 2 or id == 3:  # revenue and profit
                l[id + 1] = np.float32(((np.float32(j.text.strip().replace(',', '')) + 1 - 1 )/1000).round(4))
                if np.isnan(l[id + 1]) or np.isinf(l[id + 1]):
                  raise ValueError
              else:  # company name
                l[id + 1] = remove_suffix(j.text)
            except (ValueError, AttributeError): # Incase revenue or profit is N.A, set it to none
                l[id + 1] = None
                wrong.append(cnt - 1)
            except IndexError:
                break
          # Add the new row to the DataFrame
          web_df.loc[len(web_df)] = {data_names[0]: l[0], data_names[1]: cnt, data_names[2]: l[2], data_names[3]: l[3], data_names[4]: l[4]}

    print(l[0])
    

    web_df = web_df.drop(wrong)
    wrong_cnt += len(wrong)
    data_df = pd.concat([data_df, web_df])


  for year in range(2013, 2023):
    wrong = []
    file_df = pd.DataFrame()
    col_names = ['Rank', 'Company Name', 'Revenues\n($millions)', 'Profits\n($millions)']
    if year == 2016:
      col_names = ['Rank', 'Company Name', 'Revenues', 'Profits']
    
    file_df = pd.read_excel(f'{os.path.join(os.getcwd(),"Data")}/Fortune-500-US-List-{year}.xlsx', sheet_name = 'Data', skiprows=7, nrows=501, usecols = col_names)

    

    file_df = file_df.rename(columns={col_names[1]: data_names[2], col_names[2]: data_names[3], col_names[3]: data_names[4]})

    file_df.insert(0, data_names[0], year)
    file_df[data_names[1]] = file_df[data_names[1]].astype(int)
    file_df[data_names[2]] = [remove_suffix(d) for d in file_df[data_names[2]].astype(str)]
    # Convert 'Revenue' to float, handling both positive and negative values
    file_df[data_names[3]] = pd.to_numeric(file_df[data_names[3]].replace({'\$': '', ',': ''}, regex=True), errors='coerce') # some companies have no revenue or no profit. In that case, we just replace it with NAN
    file_df[data_names[4]] = pd.to_numeric(file_df[data_names[4]].replace({'\$': '', ',': ''}, regex=True), errors='coerce')

    for id in range(file_df.shape[0]):
      try:
        file_df.loc[id, data_names[3]] = (np.float32(file_df.loc[id, data_names[3]])/1000).round(4)
        if np.isnan(file_df.loc[id, data_names[3]]) or np.isinf(file_df.loc[id, data_names[3]]):
          raise ValueError
        file_df.loc[id, data_names[4]] = (np.float32(file_df.loc[id, data_names[4]])/1000).round(4)
        if np.isnan(file_df.loc[id, data_names[4]]) or np.isinf(file_df.loc[id, data_names[4]]):
          raise ValueError
      except ValueError:
        wrong.append(id)

    file_df = file_df.drop(wrong)
    wrong_cnt += len(wrong)
    data_df = pd.concat([data_df, file_df])
    print(year)


  for id, row in data_df.iterrows():
    cur.execute(f'''INSERT INTO {data_names[2]} ({data_names[2]}) VALUES (?)''', (row[2], ))
    cur.execute(f'''SELECT id FROM {data_names[2]} WHERE ({data_names[2]}) = (?) ''', (row[2], ))
    val = cur.fetchone()[0]
    cur.execute(f'''INSERT INTO Lab
          ({data_names[0]}, {data_names[1]}, {data_names[2]}, {data_names[3]}, {data_names[4]})
          VALUES ( ?, ?, ?, ?, ? )''', (row[0], row[1], val, row[3], row[4]) )
          
  value = np.array(data_df[[data_names[0], data_names[1], data_names[3], data_names[4]]], dtype = np.float32).T.tolist()
  with open('values.json', 'w') as f:
      json.dump(value, f)


  db.commit()
  db.close()

