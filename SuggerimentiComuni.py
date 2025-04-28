import pandas as pd
import numpy as np
import os 
from tqdm import tqdm
from fuzzywuzzy import fuzz, process

# Comments are structured as follows:
# Title (Execution time in local CPU)
    # specific comment

#######################################
# Preparation dati Comunali (472ms)
istat = pd.read_csv('data/codici_istat.csv', sep=';', encoding='Windows-1252')
base = pd.read_excel('data/tassonomia_comuni.xlsx').rename(columns={'Azione':'azione'})
piani_comunali = pd.read_parquet('data/piani_comunali.gzip')

tassonomia = pd.merge(base,
                      piani_comunali[['ID_tassonomia', 'azione', 'codice_macro', 
                                      'descrizione_codice_macro', 'numero_codice_campo', 
                                      'descrizione_codice_campo']].value_counts().reset_index().sort_values(by='ID_tassonomia'),
                     on = 'azione', 
                     how= 'right')
    
fp = 'outputComuni/'
os.makedirs(fp, exist_ok=True)

#######################################
# List of actions to eliminate (low frequency) (8ms)
view = tassonomia.sort_values(by='count').rename(columns={'count':'Frequenza'})
# asking: Select an upper threshold for the frequencies of rarely used actions 
soglia = input('Soglia superiore per la frequenza di azioni raramente usate:')

bassa_frequenza = view[view['Frequenza'] <= int(soglia)]
bassa_frequenza.to_csv(f'{fp}azioni_comuni_eliminare.csv')
print(f'Azioni con meno di {soglia} osservazioni salvate in {fp}azioni_comuni_eliminare.csv')
print(bassa_frequenza.head())

########################################
# List of actions to merge  (28.97s)
# (suggerendo possibili errori, confusioni o incompletezze nella compilazione del Comune che 
# fa uso della tassonomia)

# Disclaimer: questo codice prende quasi 30 secondi a causa delle numerose operazioni
# di string matching e di pulizia del testo. È consigliabile pre-calcolare 
# le somiglianze e disporle all'utente
# direttamente dal file salvato anziché processando i dati.
print('Calcolo della similarità tra azioni categorizzate con voci diverse')
from pulitore import Pulitore, ascificatore
stop = pd.read_csv('data/stopwords.txt')
nomi = pd.read_csv('data/nomi_di_comuni.txt')
spec = pd.read_csv('data/termini_specifici.txt')
p = Pulitore(nomi, spec, stop)

ID_tassonomia_1 = []
ID_tassonomia_2 = []
Azione_1 = []
Azione_2 = []
Levenshtein = []
for c in tqdm(piani_comunali.comune_breve.unique()):
    view = piani_comunali[piani_comunali.comune_breve == c]

    l_a = view.ID_tassonomia.unique().tolist() #insieme di azioni pubblicate dal comune    
    
    seen = []    

    for i in l_a:
        for j in l_a:        
            if i == j:
                continue            
            first = l_a.pop(0)
            #print(l_a)
            a = view[view.ID_tassonomia == first].titolo.values
            choices = view[view.ID_tassonomia.isin(l_a)].titolo.values
            choices = [' '.join(p.simple_tokenizer(ascificatore(option))) for option in choices]            
            
            # Scenario in cui ci sono multiple azioni sotto la stessa categoria in posizione j              
            if a.shape[0] > 1: 
                a = [' '.join(p.simple_tokenizer(ascificatore(option))) for option in a]
                for azione in a:                    
                    if azione == 'nan':
                        continue
                    
                    res = process.extractOne(azione, choices, scorer=fuzz.token_sort_ratio)                    
                    if res[1] < 75:  #se il risultato è scadente, si passa alla prossima iterazione
                        continue
                    
                    ID_tassonomia_1.append(first)
                    Azione_1.append(azione)
                    Azione_2.append(res[0])
                    Levenshtein.append(res[1])  

                    # È fondamentale recuperare la categoria della seconda voce, 
                    # identificata come la più simile, ma process.extractOne fornisce la posizione. 
                    # Il recupero avviene qui sotto:
                    match = process.extractOne(res[0], view[view.ID_tassonomia.isin(l_a)].titolo.values)[0]
                    second = view[ (view.ID_tassonomia.isin(l_a)) & (view.titolo==match)].ID_tassonomia.values[0]
                    ID_tassonomia_2.append(second)
                                
            # Scenario in cui c'è una sola azione sotto la categoria in posizione j
            else: 
                a = ' '.join(p.simple_tokenizer(ascificatore(a[0])))                
                if a == 'nan':
                    continue
                    
                res = process.extractOne(a, choices, scorer=fuzz.token_sort_ratio)                    
                if res[1] < 75: 
                    continue
                ID_tassonomia_1.append(first)
                Azione_1.append(a)
                Azione_2.append(res[0])
                Levenshtein.append(res[1])

                match = process.extractOne(res[0], view[view.ID_tassonomia.isin(l_a)].titolo.values)[0]
                second = view[ (view.ID_tassonomia.isin(l_a)) & (view.titolo==match)].ID_tassonomia.values[0]
                ID_tassonomia_2.append(second)
azioni_diversimili = pd.DataFrame({'ID_tassonomia_1':ID_tassonomia_1,
                     'titolo_1':Azione_1,
                      'ID_tassonomia_2':ID_tassonomia_2,
                     'titolo_2':Azione_2,
                     'Levenshtein':Levenshtein})
summary = (
    azioni_diversimili
    .groupby(['ID_tassonomia_1', 'ID_tassonomia_2'])
    .agg(
        count=('titolo_1', 'count'),
        titoli_1_list=('titolo_1', lambda x: list(set(x))),
        titoli_2_list=('titolo_2', lambda x: list(set(x)))
    )
    .reset_index()
)

summary = summary.rename(columns={'count':'Frequenza'})
summary.sort_values(by='Frequenza',ascending=False).to_csv(f'{fp}azioni_simili_unire.csv')
print(f'Le azioni, somiglianti per descrizione ma con voci diverse della tassonomia, sono salvate in {fp}azioni_simili_unire.csv')
print(summary.head())

########################################
# List of actions to "create", or actually split into smaller categories due to high frequency of use
view = tassonomia.sort_values(by='count').rename(columns={'count':'Frequenza'})
# asking: Select a lower threshold for the frequencies of rarely used actions 
soglia = input('Soglia inferiore per la frequenza di azioni usate spesso:')

bassa_frequenza = view[view['Frequenza'] >= int(soglia)]
bassa_frequenza.to_csv(f'{fp}azioni_da_dividere.csv')
print(f'Azioni con più di {soglia} osservazioni salvate in {fp}azioni_da_dividere.csv')
print(bassa_frequenza.head())
