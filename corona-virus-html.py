import dominate
import csv
import os
import string
import random
import requests
import threading
import calendar
import datetime
import json 
import pandas as pd
import _thread
import collections
from tabulate import tabulate
import matplotlib.pyplot as plt
import operator
from collections import OrderedDict
from dominate.tags import *
from dominate.util import raw
import html
from mako.template import Template
import numpy as np


provincie = {}
regioni ={}
a_lock=threading.Lock()

def toInt(s):
    if s :
        return int(s)
    return 0



def updateForProvincie(d):
    CSV_URL="https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province-"+d.strftime("%Y%m%d")+".csv"
    with requests.Session() as s:
        print ("Load url %s" % CSV_URL) 
        download = s.get(CSV_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')     
        for record in cr:
            pr = record["sigla_provincia"]
            entry ={"date":d, "tot":toInt(record["totale_casi"]), "regione":record["denominazione_regione"]}
            a_lock.acquire()
            if (pr not in provincie):
                provincie[pr]=[]
        
            provincie[pr].append(entry)
            a_lock.release()
       
def updateForRegioni(d):
    #https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-20200224.csv
    CSV_URL="https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-"+d.strftime("%Y%m%d")+".csv"
    with requests.Session() as s:
        print ("Load url %s" % CSV_URL) 
        download = s.get(CSV_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')     
        for record in cr:
            
            regione = record["denominazione_regione"]
            # Initialize key list  
            key_traslate = {
                
                "totale_casi":"Casi","tamponi":"Tamponi",
                "ricoverati_con_sintomi":"Ricoverati",
                            "terapia_intensiva": "Ti","totale_ospedalizzati":"Ospedalizzati","isolamento_domiciliare":"Isolamento","totale_positivi":"Positivi","nuovi_positivi":"Nuovi casi","dimessi_guariti":"Guariti","deceduti":"Deceduti"} 
  
            # Using list comprehension + get() 
            # Selective key values in dictionary 
            entry = {}
            entry["date"] = d;
            
            
            for k in key_traslate.keys() :
                entry[key_traslate[k]] = toInt(record[k])
           
            
           
            #entry ={"date":d, "tot":toInt(record["totale_casi"]), "regione":record["denominazione_regione"]}
            a_lock.acquire()
            if (regione not in regioni):
                regioni[regione]=[]
        
            regioni[regione].append(entry)
            a_lock.release()
       
def printAnalysisForProvincie(regione):
    for prov in provincie.keys():
        if (provincie[prov][0])["regione"] == regione :

            print ("******************************" )
            print ("******** provincia %s ********" % prov)
            sorted_list = sorted(provincie[prov], key=lambda k: k['date']) 

            data_frame= pd.DataFrame.from_dict(sorted_list)   
        
            data_frame["inc"] = data_frame['tot'].diff(1)
            data_frame["perc"] = data_frame['tot'].pct_change(1)
        
            print (data_frame)
        
       
            data_frame.plot(x ='date', y='tot', figsize=(13,8), rot=30, title=prov)	


def getDataFrameForRegione(regione):
    print ("******************************" )
    print ("******** Regione %s ********" % regione)
    sorted_list = sorted(regioni[regione], key=lambda k: k['date']) 
    data_frame= pd.DataFrame.from_dict(sorted_list)       
   # data_frame["inc"] = data_frame['Positivi'].diff(1)
    data_frame["Incr. Positivi (%)"] = data_frame['Positivi'].pct_change(1)
    data_frame["Incr. TI"] = data_frame['Ti'].diff(1)
    data_frame["Incr. Ospe"] = data_frame['Ospedalizzati'].diff(1)
    return data_frame
 




    
threads_provincie = []
threads_regioni = []

rangeGiorni=30
for i in range(0,rangeGiorni):
    d =datetime.date.today()-datetime.timedelta(i)
    t = threading.Thread(target=updateForProvincie, args=(d,))
    t_r =threading.Thread(target=updateForRegioni, args=(d,))
    threads_provincie.append(t)
    threads_regioni.append(t_r)


    t.start()
    t_r.start()
  
for i in range(0,rangeGiorni):
    threads_provincie[i-1].join()
    threads_regioni[i-1].join()
    
regioniDataFrame = {}
for k in regioni.keys():
    regioniDataFrame[k]=getDataFrameForRegione(k)
    
 





regioniT = {}
for k in regioni.keys():
    data_frame = regioniDataFrame[k]
    dic = data_frame.to_dict()
    
    dates =dic["date"]
    positivi = dic["Positivi"]
   
    t = tabulate(data_frame,headers='keys', tablefmt="html");
    regioniT[k] = {}
    regioniT[k]["table"]=t.replace("<table>", "<table class=\"table table-striped table-sm\">")
    regioniT[k]["dates"]= [x.isoformat() for x in dates.values()]
    regioniT[k]["positivi"]= [x for x in positivi.values()]
    regioniT[k]["ospedalizzati"]= [x for x in dic["Ospedalizzati"].values()]
    
    
    regioniT[k]["inc"]= [np.nan_to_num(x) for x in dic["Nuovi casi"].values()]
    regioniT[k]["ti"]= [np.nan_to_num(x) for x in dic["Ti"].values()]
    regioniT[k]["inc_ti"]= [np.nan_to_num(x) for x in dic["Incr. TI"].values()]
    
    print (k)
    print (10*"******")
    
    
    

_template = Template(filename='./corona.virus.template.html',input_encoding='utf-8',output_encoding='utf-8'
                     )
with open('corona-virus.html', 'w') as f:
    f.write((_template.render_unicode(regioni=regioniT)))
