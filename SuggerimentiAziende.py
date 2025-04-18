import pandas as pd
import numpy as np
import os 
from tqdm import tqdm
from fuzzywuzzy import fuzz, process

# I commenti sono strutturati in:
# Titolo (Tempo di esecuzione in una CPU locale)
    # specifica
#######################################
# Preparazione dati delle organizzazioni (112ms)
#si deve rimuovere una piccola parte dei dati che era originalmente chiamata in modo 
# simile a quella dei comuni, 'ID_tassonomia', seppur avendo una diversa tassonomia 

piani_aziendali = pd.read_parquet('data/piani_aziendali.gzip').dropna(subset='Label 0').drop(columns='ID_tassonomia')  
piani_aziendali['Label 0'] = piani_aziendali['Label 0'].astype(int)

tassonomia = piani_aziendali[['Label 0','codice_macro', 
                 'descrizione_codice_macro', 'numero_codice_campo',
                'descrizione_codice_campo']].value_counts().reset_index().rename(columns={'Label 0':'ID_tassonomia'}
                                                                                ).sort_values(by='ID_tassonomia'
                                                                                             ).rename(columns={'count':'Frequenza della combinazione nell\'intero dataset'})

c = []
for i in tassonomia[['ID_tassonomia', 'codice_macro', 'numero_codice_campo']].values:    
    view = piani_aziendali[(piani_aziendali['Label 0'] == i[0]) & (piani_aziendali['codice_macro'] == i[1]) & (piani_aziendali['numero_codice_campo'] == i[2])]
    c.append(view.ID_organizzazione.unique().shape[0])
tassonomia['Numero di organizzazioni che ne hanno fatto uso nel dataset'] = c

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
# Azioni di basso utilizzo considerato l'intero dataset (8ms)
bassa_frequenza = tassonomia.sort_values(by='Frequenza della combinazione nell\'intero dataset')
soglia = input('Mostrare le azioni utilizzate meno di __ volte:')
bassa_frequenza[bassa_frequenza['Frequenza della combinazione nell\'intero dataset'] <= int(soglia)].to_csv(f'{fp}bassa_frequenza.csv')
print(f'Osservazioni con meno di {soglia} righe salvate in {fp}bassa_frequenza.csv')
print(bassa_frequenza.head())

    #Si può ovviamente invertire la logica e selezionare tutte le azioni con frequenza 
    # maggiore di (>=) una data soglia. O semplicemente ordinare la visualizzazione delle
    # azioni dal maggiore al minore. 

#######################################
# Azioni ordinate per utilizzo di UNA organizzazione (57ms)

# e.g. '12345055' o '5055'
print('L\'ID dell\'organizzazione si trova più facilmente se si specificano le ultime 4 cifre dell\'identificativo.')
user_input = input("ID dell'organizzazione da analizzare (inserire l\'ID specifico di una organizzazione coinvolta):") 
choices = piani_aziendali.ID_organizzazione.astype(str).unique()  

azienda = process.extractOne(str(user_input.strip()), choices, scorer=fuzz.ratio)[0]
focus = piani_aziendali[piani_aziendali.ID_organizzazione==azienda]

rank = focus.value_counts(subset=['Label 0', 'codice_macro', 'descrizione_codice_macro', 'numero_codice_campo', 'descrizione_codice_campo']).reset_index().rename(columns=
                                                                            {'Label 0':'ID_tassonomia', 
                                                                             'count':'Frequenza nell\'organizzazione'})

rank = pd.merge(rank, tassonomia[['ID_tassonomia', 
                                  'Frequenza della combinazione nell\'intero dataset', 
                                  'Numero di organizzazioni che ne hanno fatto uso nel dataset']], how='left')
rank.to_csv(f'{fp}{azienda}.csv')
print(f'Le frequenze di azioni {fp}{azienda}.csv')
print(rank.head())

#######################################
# Serie storica per una lista di voci della tassonomia selezionate dall'utente (125ms)
    # e.g. di input precompilato:
# user_inputs = [11630769,
#                11630764,
#                11630751,
#                11630770]               

user_inputs = []

while True:
    entry = input("Azione da visualizzare (scrivi 'END' per terminare la lista): ")
    if entry.strip() == "END":
        break
    user_inputs.append(entry.strip())

print("Voci inserite:", user_inputs)
    

choices = tassonomia.ID_tassonomia

    # identificazione degli input tra le scelte possibili
if len(user_inputs) > 1:
    azione = [process.extract(str(a), choices)[0][0] for a in user_inputs ]
elif len(user_inputs): 
    azione = [process.extract(str(user_inputs[0]), choices)[0][0]]

    # preparazione dati per la visualizzazione
def wrapper(text, words_per_line=3):    
    words = text.replace('/',' - ').split()
    lines_per_chunk = words_per_line%len(words) + 1  
    lines = [' '.join(words[i:i+words_per_line]) for i in range(0, len(words), words_per_line)]    
    chunks = ['<br>'.join(lines[i:i+lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]    
    return chunks[0]
    
storia = pd.DataFrame(columns=['anno_compilazione'])
for a in azione:
    t = piani_aziendali[piani_aziendali['Label 0'] == a]
    #si deve "rompere" a causa della frequente lunghezza eccessiva
    try:
        a = wrapper(a)
    except:
        a
    t = t.anno_compilazione.value_counts().reset_index().rename(columns={'count':a})
    
    if storia.shape[0]==0:
        storia = t
    else:
        storia = pd.merge(storia, t, on='anno_compilazione', how='left')    
storia = storia.fillna(0).sort_values(by='anno_compilazione')
storia.to_csv(f'{fp}serie_storica.csv')
print(f'Serie storica per le azioni selezionate salvata in {fp}serie_storica.csv')
print(storia.head())
print()
    # visualizzazione 
import plotly.express as px

df_long = storia.melt(id_vars='anno_compilazione', value_vars=storia,
                 var_name='Voce della tassonomia', value_name='Value')
fig = px.line(
    df_long,
    x='anno_compilazione',
    y='Value',
    color='Voce della tassonomia',
    markers=True,
)
    
fig.update_layout(
    xaxis_title="Annualità",
    yaxis_title="Frequenza di utilizzo"
)
fig.write_html(f"{fp}serie_storica_azione.html")
print(f'Visualizzazione interattiva salvata in {fp}serie_storica_azione.html')

########################################
# Azioni simili ma categorizzate con diverse voci  (2m 45.61s)
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
for c in tqdm(piani_aziendali.ID_organizzazione.unique()):
    view = piani_aziendali[piani_aziendali.ID_organizzazione == c]

    l_a = view['Label 0'].unique().tolist() #insieme di azioni pubblicate dall'organizzazione    
    
    seen = []    

    for i in l_a:
        for j in l_a:        
            if i == j:
                continue            
            first = l_a.pop(0)
            #print(l_a)
            a = view[view['Label 0'] == first].descrizione.fillna(0).values            
            choices = view[view['Label 0'].isin(l_a)].descrizione.fillna(0).values
            choices = [' '.join(p.simple_tokenizer(ascificatore(option))) if option != 0 else option for option in choices]            
            # Nei dati delle organizzazioni si nota che il titolo è frequentemente
            # soggetto a duplicazione per azioni ben diverse, fenomeno che avviene
            # notevolmente di meno nei dati dei Comuni. Di conseguenza, 
            # nel caso delle organizzazioni si usa la descrizione (tokenizzata)
            # per individuare azioni di diverse categorie implementate in maniera simile. 
             
            
            # Scenario in cui ci sono multiple azioni sotto la stessa categoria in posizione j                          
            if a.shape[0] > 1: 
                
                a = [' '.join(p.simple_tokenizer(ascificatore(option))) if option != 0 else option for option in a]
                for azione in a:
                    if azione == 0: #descrizione vuota, inutile paragonare 
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
                    match = process.extractOne(res[0], view[view['Label 0'].isin(l_a)].descrizione.values)[0]
                    second = view[ (view['Label 0'].isin(l_a)) & (view.descrizione==match)]['Label 0'].values[0]
                    ID_tassonomia_2.append(second)
            
            # Scenario in cui c'è una sola azione sotto la categoria in posizione j
            else: 
                if a == 0: #descrizione vuota, inutile paragonare 
                        continue
                a = ' '.join(p.simple_tokenizer(ascificatore(a[0])))                
                
                res = process.extractOne(a, choices, scorer=fuzz.token_sort_ratio)                    
                if res[1] < 75: 
                    continue
                ID_tassonomia_1.append(first)
                Azione_1.append(a)
                Azione_2.append(res[0])
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
    .agg(
        count=('descrizione_1', 'count'),
        titoli_1_list=('descrizione_1', lambda x: list(set(x))),
        titoli_2_list=('descrizione_2', lambda x: list(set(x)))
    )
    .reset_index()
)

summary = summary.rename(columns={'count':'Frequenza'})
summary.sort_values(by='Frequenza',ascending=False).to_csv(f'{fp}azioni_diversimili.csv')
print(f'Tabella di azioni somiglianti ma che hanno diverse voci nella tassonomia salvata in {fp}azioni_diversimili.csv')
print(summary.head())
