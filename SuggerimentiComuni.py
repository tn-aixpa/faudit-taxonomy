import pandas as pd
import numpy as np
import os 
from tqdm import tqdm
from fuzzywuzzy import fuzz, process
import simplemma
import re
import string
from unidecode import unidecode
from simplemma import is_known, text_lemmatizer, simple_tokenizer

class Pulitore:
    def __init__(self, 
                 luoghi, 
                 specificità, 
                 stopwords
                ):
        self.luoghi = luoghi
        self.specificita = specificità
        self.stopwords = stopwords
    
    def simple_tokenizer(self, text):
        # Tokenizza un testo dal quale è già stata rimossa la punteggiatura
        return simple_tokenizer(re.sub('[%s]' % re.escape(string.punctuation + '’и1234567890–м·…'), ' ' , text.lower()))
    
    def lemmatize(self, word, lang='it'):
        # usa simplemma per lemmatizzare
        return unidecode(simplemma.lemmatize(word, lang=lang))           
    
    def clean_text(self, t, second_iter=False):
    
        s = self.simple_tokenizer(t)
        
        r = []
        
        for i in s:
            i = i.lower()
            if i in self.stopwords or len(i) <= 1:
                continue
            if is_known(i, lang='it'):
                r.append(self.lemmatize(i, lang='it'))

            elif i in self.specificita:
                r.append(i)
                
            elif i in self.luoghi:  # Escludere i nomi dei comuni o luoghi nei dati? Basta ghiacciare questo elif
                r.append(i)
                
            elif is_known(i, lang='en'):
                r.append(self.lemmatize(i, lang='en'))
                
            elif is_known(i, lang='de'):
                r.append(self.lemmatize(i, lang='de'))
                            
        return r

def ascificatore(s):
    return unidecode(' '.join([c for c in re.split(r'[\r\n\t]+', s) if s.strip()]).encode('ascii', 'ignore').decode())


# Comments are structured as follows:
# Title (Execution time in local CPU)
    # specific comment

def taxonomy_suggestions(project, piani_comunali, tassonomia, stopwords, nomi, termini):
    piani_comunali = piani_comunali.as_df()
    tassonomia = tassonomia.as_df()
    stop = stopwords.as_df()
    nomi = nomi.as_df()
    spec = termini.as_df()

    (frequenza, summary) = main(piani_comunali, tassonomia, stop, nomi, spec)
    project.log_dataitem('tassonomia_comuni_azioni_frequenza', kind="table", data=frequenza)
    project.log_dataitem('tassonomia_comuni_azioni_unire', kind="table", data=summary)


def main(piani_comunali, tassonomia, stop, nomi, spec):    
    #######################################
    # Preparation dati Comunali (472ms)
    tassonomia = pd.merge(piani_comunali.ID_tassonomia.value_counts().reset_index().rename(columns={'count':'Frequenza delle azioni'}), tassonomia)
    
    #######################################
    # List of actions to eliminate (low frequency) (8ms)
    # asking: Select an upper threshold for the frequencies of rarely used actions 
    
    frequenza = tassonomia # [tassonomia['Frequenza delle azioni'] <= soglia]
    # bassa_frequenza.to_csv(f'azioni_eliminare.csv', sep=';', index=False)
    
    ########################################
    # List of actions to merge  (17s)
    # (suggerendo possibili errori, confusioni o incompletezze nella compilazione del Comune che 
    # fa uso della tassonomia)
    
    # Disclaimer: questo codice prende quasi 30 secondi a causa delle numerose operazioni
    # di string matching e di pulizia del testo. È consigliabile pre-calcolare 
    # le somiglianze e disporle all'utente
    # direttamente dal file salvato anziché processando i dati.
    print('Calcolo della similarità tra azioni categorizzate con voci diverse')

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
             Percentuale_di_similarità=('Levenshtein', lambda x: np.nanmean(list(x)))    
        )
        .reset_index()
    )
    
    summary = summary.rename(columns={'count':'Frequenza'})
    summary = summary.sort_values(by='Frequenza',ascending=False)
    summary.to_csv(f'azioni_unire.csv', sep=';', index=False)
    print(f'Azioni somiglianti ma che hanno diverse voci nella tassonomia salvata in azioni_unire.csv')
    
    ########################################
    # List of actions to "create", or actually split into smaller categories due to high frequency of use
    # asking: Select a lower threshold for the frequencies of rarely used actions 
    # azioni_dividere = tassonomia[tassonomia['Frequenza delle azioni'] >= soglia_utilizzo]
    # azioni_dividere.to_csv(f'azioni_da_dividere.csv', sep=';', index=False)
    # print(f'Azioni con più di {soglia} osservazioni salvate in azioni_dividere.csv')
    
    return (frequenza, summary)