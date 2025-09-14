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
    try:
        return unidecode(' '.join([c for c in re.split(r'[\r\n\t]+', s) if s.strip()]).encode('ascii', 'ignore').decode())
    except:
        return str(s)

def taxonomy_suggestions(project, piani_aziendali, tassonomia, stopwords, nomi, termini):
    piani_aziendali = piani_aziendali.as_df()
    tassonomia = tassonomia.as_df()
    stop = stopwords.as_df()
    nomi = nomi.as_df()
    spec = termini.as_df()

    (frequenza, summary) = main(piani_aziendali, tassonomia, stop, nomi, spec)
    project.log_dataitem('tassonomia_aziende_azioni_frequenza', kind="table", data=frequenza)
    project.log_dataitem('tassonomia_aziende_azioni_unire', kind="table", data=summary)

def main(piani_aziendali,tassonomia, stop, nomi, spec):
    tassonomia = pd.merge(piani_aziendali['Label 0'].value_counts().reset_index().rename(columns={'count':'Frequenza delle azioni', 'Label 0':'ID_tassonomia'}), tassonomia)

    frequenza = tassonomia
    print('Calcolo della similarità tra azioni categorizzate con voci diverse')
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
                choices2 = [' '.join(p.simple_tokenizer(ascificatore(option))) if option != 0 else option for option in choices] 
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
                elif len(a) == 1 and a[0] != 0: 
    
                    a2 = ' '.join(p.simple_tokenizer(ascificatore(a[0])))                
                    
                    res = process.extractOne(a2, choices2, scorer=fuzz.token_set_ratio)                    
                    
                    if res is None or res[1] < 75: 
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
             Percentuale_di_similarità=('Levenshtein', lambda x: np.nanmean(list(x)))
        )
        .reset_index()
    )
    
    
    summary = summary.rename(columns={'count':'Frequenza'})
    summary.sort_values(by='Frequenza',ascending=False)
    return (frequenza, summary)