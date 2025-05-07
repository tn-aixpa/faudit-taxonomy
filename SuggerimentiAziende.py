import pandas as pd
import numpy as np
import os 
from tqdm import tqdm
from fuzzywuzzy import fuzz, process

# I commenti sono strutturati in:
# Titolo (Tempo di esecuzione in una CPU locale)
    # specifica
#######################################
# Preparation dati Aziendali (112ms)
#si deve rimuovere una piccola parte dei dati che era originalmente chiamata in modo 
# simile a quella dei comuni, 'ID_tassonomia', seppur avendo una diversa tassonomia 

piani_aziendali = pd.read_parquet('data/piani_aziendali.gzip')
tassonomia = pd.read_csv('data/tassonomia_aziende.csv', sep=';')
tassonomia = pd.merge(piani_aziendali['Label 0'].value_counts().reset_index().rename(columns={'count':'Frequenza delle azioni', 'Label 0':'ID_tassonomia'}), tassonomia)
# I dati delle organizzazioni (aziende) sono più complessi di quelli comunali. 
# Ogni osservazione può avere più di una categoria nella tassonomia del Family Audit, 
# e può avere più di un codice macro e più di un codice campo. 

# Ci sono in totale 107 voci utilizzate dalle organizzazioni, e se combinate con i codici 
# macro e codici campo c'è un totale di 512 combinazioni utilizzate che si presentano nei dati.

# Al fine di una rappresentazione semplice per le statistiche descrittive, è necessario utilizzare
# solo la prima (e più importante) categoria della tassonomia attribuita a un'azione, che si posiziona 
# nella colonna 'Label 0'

fp = 'outputOrganizzazioni/'
os.makedirs(fp, exist_ok=True)

#######################################
#  List of actions to eliminate (low frequency)  (8ms)
soglia = input('Mostrare le azioni utilizzate meno di __ volte:')
bassa_frequenza = tassonomia[tassonomia['Frequenza di utilizzo dell\'azione'] <= int(soglia)]
bassa_frequenza.to_csv(f'{fp}azioni_eliminare.csv', sep=';', index=False)
print(f'Osservazioni con meno di {soglia} righe salvate in {fp}azioni_eliminare.csv')
print(bassa_frequenza.head())

    #Si può ovviamente invertire la logica e selezionare tutte le azioni con frequenza 
    # maggiore di (>=) una data soglia. O semplicemente ordinare la visualizzazione delle
    # azioni dal maggiore al minore. 

########################################
# List of actions to merge (21s)
# (suggerendo possibili errori, confusioni o incompletezze nella compilazione dell'organizzazione che 
# fa uso della tassonomia)

# Disclaimer: questo codice prende quasi 3 minuti a causa delle numerose operazioni
# di string matching e di pulizia del testo. È consigliabile pre-calcolare 
# le somiglianze e disporle all'utente
# direttamente dal file salvato anziché processando i dati on demand. 
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
aziende = list(piani_aziendali.ID_organizzazione.unique())#[:10] #D
for c in tqdm(aziende):
    view = piani_aziendali[piani_aziendali.ID_organizzazione == c]

    l_a = view['Label 0'].fillna(0).drop_duplicates().tolist() #insieme di categorie delle azioni pubblicate dall'organizzazione    
    
    for i in l_a:
        for j in l_a:        
            if i == j:
                continue            
            first = l_a.pop(0) # si parte dal primo elemento dell'insieme vs tutto il rimanente
            #print(l_a)
            a = view[(view['Label 0'] == first) & (~view['Label 0'].isin(l_a))].descrizione.drop_duplicates().fillna(0).values
            if a.shape[0] > 1: 
                a = a.tolist()
        
            choices = view[view['Label 0'].isin(l_a)].descrizione.drop_duplicates().fillna(0).values
            choices2 = [' '.join(p.simple_tokenizer(ascificatore(option))) for option in choices] 
            # Nei dati delle organizzazioni si nota che il titolo è frequentemente
            # soggetto a duplicazione per azioni ben diverse, fenomeno che avviene
            # notevolmente di meno nei dati dei Comuni. Di conseguenza, 
            # nel caso delle organizzazioni si usa la descrizione (tokenizzata)
            # per individuare azioni di diverse categorie implementate in maniera simile. 
                         
            # Scenario in cui ci sono multiple decsrizioni sotto la stessa categoria in posizione j                          
            if len(a) > 1: 
                
                a2 = [' '.join(p.simple_tokenizer(ascificatore(option))) if option != 0 else option for option in a]                 
                
                for azione in range(len(a2)):
                    if a2[azione] == 0: #descrizione vuota, inutile paragonare 
                        continue
                        
                    res = process.extractOne(a2[azione], choices2, scorer=fuzz.token_set_ratio)                                    
                    
                    if res[1] < 75:  #se il risultato è scadente, si passa alla prossima iterazione
                        continue
                    
                    ID_tassonomia_1.append(first)                    
                    Azione_1.append(a[azione])
                    
                    idx = choices2.index(res[0]) #indice di dove si trova il miglior match nella lista così da ritirarlo nella versione originale                
                    Azione_2.append(choices[idx])
                                        
                    Levenshtein.append(res[1])  
                    
                    # È fondamentale recuperare la categoria della seconda voce, 
                    # identificata come la più simile, ma process.extractOne fornisce la posizione. 
                    # Il recupero avviene qui sotto:
                    match = process.extractOne(res[0], view[view['Label 0'].isin(l_a)].descrizione.values, scorer=fuzz.token_set_ratio)[0]
                    second = view[ (view['Label 0'].isin(l_a)) & (view.descrizione==match)]['Label 0'].values[0]
                    ID_tassonomia_2.append(second)
            
            # Scenario in cui c'è una sola descrizione sotto la categoria in posizione j
            elif len(a) == 1: 

                a2 = ' '.join(p.simple_tokenizer(ascificatore(a[0])))                
                
                res = process.extractOne(a2, choices2, scorer=fuzz.token_set_ratio)                    
                
                if res[1] < 75: 
                    continue
                    
                ID_tassonomia_1.append(first)                
                Azione_1.append(a[0])

                idx = choices2.index(res[0]) #indice di dove si trova il miglior match nella lista così da ritirarlo nella versione originale
                
                Azione_2.append(choices[idx])
                Levenshtein.append(res[1])
                
                match = process.extractOne(res[0], view[view['Label 0'].isin(l_a)].descrizione.values, scorer=fuzz.token_set_ratio)[0]
                second = view[ (view['Label 0'].isin(l_a)) & (view.descrizione==match)]['Label 0'].values[0]
                ID_tassonomia_2.append(second)
                
azioni_diversimili = pd.DataFrame({'ID_tassonomia_1':ID_tassonomia_1,
                                   'descrizione_1':Azione_1,
                                   'ID_tassonomia_2':ID_tassonomia_2,
                                   'descrizione_2':Azione_2,
                                   'Levenshtein':Levenshtein})

summary = (
    azioni_diversimili
    .groupby(['ID_tassonomia_1', 'ID_tassonomia_2'])
    .agg(count=('descrizione_1', 'count'),
         descrizione_1_list=('descrizione_1', lambda x: x if isinstance(x, str) else ' | '.join(x).replace('\n', ' ')),         
         descrizione_2_list=('descrizione_2', lambda x: x if isinstance(x, str) else ' | '.join(x).replace('\n', ' ')),         
         Percentuale_di_similarità=('Levenshtein', lambda x: x)
    )
    .reset_index()
)


summary = summary.rename(columns={'count':'Frequenza'})
summary.sort_values(by='Frequenza',ascending=False).to_csv(f'{fp}azioni_unire.csv', sep=';', index=False)
print(f'Tabella di azioni somiglianti ma che hanno diverse voci nella tassonomia salvata in {fp}azioni_unire.csv')
print(summary.head())

########################################
# List of actions to "create", or actually split into smaller categories due to high frequency of use

bassa_frequenza = tassonomia[tassonomia['Frequenza di utilizzo dell\'azione'] >= int(soglia)]
soglia = input('Mostrare le azioni utilizzate più di __ volte:')
bassa_frequenza[bassa_frequenza['Frequenza di utilizzo dell\'azione'] >= int(soglia)].to_csv(f'{fp}azioni_dividere.csv', sep=';', index=False)
print(f'Osservazioni con meno di {soglia} righe salvate in {fp}azioni_dividere.csv')
print(bassa_frequenza.head())
