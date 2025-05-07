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
piani_comunali = pd.read_parquet('data/piani_comunali.gzip')
tassonomia = pd.read_csv('data/tassonomia_comuni.csv', sep=';')
tassonomia = pd.merge(piani_comunali.ID_tassonomia.value_counts().reset_index().rename(columns={'count':'Frequenza delle azioni'}), tassonomia)

fp = 'outputComuni/'
os.makedirs(fp, exist_ok=True)

#######################################
# List of actions to eliminate (low frequency) (8ms)
# asking: Select an upper threshold for the frequencies of rarely used actions 
soglia = input('Mostrare le azioni utilizzate meno di __ volte:')

bassa_frequenza = tassonomia[tassonomia['Frequenza delle azioni'] <= int(soglia)]
bassa_frequenza.to_csv(f'{fp}azioni_eliminare.csv', sep=';', index=False)
print(f'Azioni con meno di {soglia} osservazioni salvate in {fp}azioni_eliminare.csv')
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
        
    for i in l_a:
        for j in l_a:        
            if i == j:
                continue            
            first = l_a.pop(0)
            #print(l_a)
            a = view[view.ID_tassonomia == first].titolo.fillna(0).drop_duplicates().values
            choices = view[view.ID_tassonomia.isin(l_a)].titolo.fillna(0).drop_duplicates().values
            choices2 = [' '.join(p.simple_tokenizer(ascificatore(option))) for option in choices]            
            
            # Scenario in cui ci sono multiple azioni sotto la stessa categoria in posizione j              
            if a.shape[0] > 1: 
                a2 = [' '.join(p.simple_tokenizer(ascificatore(option))) for option in a]
                for azione in range(len(a2)):                    
                    if azione == 0:
                        continue
                    
                    res = process.extractOne(a2[azione], choices2, scorer=fuzz.token_sort_ratio)                    
                    if res[1] < 75:  #se il risultato è scadente, si passa alla prossima iterazione
                        continue
                    
                    ID_tassonomia_1.append(first)
                    Azione_1.append(a2[azione])
                    
                    idx = choices2.index(res[0]) #indice di dove si trova il miglior match nella lista così da ritirarlo nella versione originale                
                    Azione_2.append(choices[idx])
                                        
                    Levenshtein.append(res[1])  

                    # È fondamentale recuperare la categoria della seconda voce, 
                    # identificata come la più simile, ma process.extractOne fornisce la posizione. 
                    # Il recupero avviene qui sotto:
                    match = process.extractOne(res[0], view[view.ID_tassonomia.isin(l_a)].titolo.values)[0]
                    second = view[ (view.ID_tassonomia.isin(l_a)) & (view.titolo==match)].ID_tassonomia.values[0]
                    ID_tassonomia_2.append(second)
                                
            # Scenario in cui c'è una sola azione sotto la categoria in posizione j
            elif len(a) == 1:
                a2 = ' '.join(p.simple_tokenizer(ascificatore(a[0])))                
                    
                res = process.extractOne(a2, choices2, scorer=fuzz.token_sort_ratio)                    
                if res[1] < 75: 
                    continue
                ID_tassonomia_1.append(first)
                Azione_1.append(a[0])
                idx = choices2.index(res[0]) #indice di dove si trova il miglior match nella lista così da ritirarlo nella versione originale                
                Azione_2.append(choices[idx])
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
    .agg(count=('titolo_1', 'count'),
         titoli_1_list=('titolo_1', lambda x: x if isinstance(x, str) else ' | '.join(x).replace('\n', ' ') ),
         titoli_2_list=('titolo_2', lambda x: x if isinstance(x, str) else ' | '.join(x).replace('\n', ' ') ),
         Percentuale_di_similarità=('Levenshtein', lambda x: list(x))    
    )
    .reset_index()
)

summary = summary.rename(columns={'count':'Frequenza'})
summary.sort_values(by='Frequenza',ascending=False).to_csv(f'{fp}azioni_unire.csv', sep=';', index=False)
print(f'Azioni somiglianti ma che hanno diverse voci nella tassonomia salvata in {fp}azioni_unire.csv')
print(summary.head())

########################################
# List of actions to "create", or actually split into smaller categories due to high frequency of use
# asking: Select a lower threshold for the frequencies of rarely used actions 
soglia = input('Mostrare le azioni utilizzate più di __ volte:')
bassa_frequenza = tassonomia[tassonomia['Frequenza delle azioni'] >= int(soglia)]
bassa_frequenza.to_csv(f'{fp}azioni_da_dividere.csv', sep=';', index=False)
print(f'Azioni con più di {soglia} osservazioni salvate in {fp}azioni_dividere.csv')
print(bassa_frequenza.head())
