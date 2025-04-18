import pandas as pd
import numpy as np
import os 
from tqdm import tqdm
from fuzzywuzzy import fuzz, process

# I commenti sono strutturati in:
# Titolo (Tempo di esecuzione in una CPU locale)
    # specifica
#######################################
# Preparazione dati Comunali (472ms)
istat = pd.read_csv('data/codici_istat.csv', sep=';', encoding='Windows-1252')
base = pd.read_excel('data/tassonomia_comuni.xlsx').rename(columns={'Azione':'azione'})
piani_comunali = pd.read_parquet('data/piani_comunali.gzip')

tassonomia = pd.merge(base,
                      piani_comunali[['ID_tassonomia', 'azione', 'codice_macro', 
                                      'descrizione_codice_macro', 'numero_codice_campo', 
                                      'descrizione_codice_campo']].value_counts().reset_index().sort_values(by='ID_tassonomia'),
                     on = 'azione', 
                     how= 'right')
    
fp = 'output/'
os.makedirs(fp, exist_ok=True)

#######################################
# Azioni di basso utilizzo su TUTTI i territori partecipanti (8ms)
view = tassonomia.sort_values(by='count').rename(columns={'count':'Frequenza'})
soglia = input('Soglia superiore per la frequenza di azioni (inserire un numero):')

bassa_frequenza = view[view['Frequenza'] <= int(soglia)]
bassa_frequenza.to_csv(f'{fp}bassa_frequenza.csv')
print(f'Osservazioni con meno di {soglia} righe salvate in {fp}bassa_frequenza.csv')
print(bassa_frequenza.head())

    #Si può ovviamente invertire la logica e selezionare tutte le azioni con frequenza 
    # maggiore di (>=) una data soglia. O semplicemente ordinare la visualizzazione delle
    # azioni dal maggiore al minore. 

user_input = input('Provincia da analizzare (inserire un nome di una Provincia coinvolta):') # e.g. 'Bologna'

#######################################
# Azioni ordinate per utilizzo di UNA provincia (30ms)
choices = istat['Denominazione dell\'Unità territoriale sovracomunale \n(valida a fini statistici)'].unique()

    #Si possono scegliere più o meno opzioni, con il primo elemento [0] si seleziona la migliore scelta per somiglianza
provincia = process.extract(user_input.strip(), choices, limit=10)[0][0]  

lista_comuni = istat[istat['Denominazione dell\'Unità territoriale sovracomunale \n(valida a fini statistici)'] == provincia]['Codice Comune formato alfanumerico']

focus = piani_comunali[piani_comunali.codice_istat.isin(lista_comuni)]

rank = pd.merge(focus.ID_tassonomia.value_counts().reset_index().rename(columns={'count':'Frequenza'}).sort_values(by=['Frequenza','ID_tassonomia']), tassonomia, on ='ID_tassonomia').rename(columns={'ID_tassonomia':'Voce della tassonomia'})
    #Questo risultato può essere disposto dal valore minore al maggiore (o viceversa) della colonna "Frequenza", che è specifica al numero di azioni usate nella Provincia ricercata. 
rank.to_csv(f'{fp}{provincia}.csv')

print(f'Azioni ordinate per utilizzo della Provincia di {provincia} salvate in {fp}{provincia}.csv')
print(rank.head())
print()
#######################################
# Serie storica per una lista di voci della tassonomia selezionate dall'utente (109ms)
    # e.g. di input precompilato:
    # user_inputs = ['Agevolazioni tariffarie e contributi attivitа ricreative/culturali/aggregative/formative	',
    #                ' Adesione ai marchi familiari	',
    #                'Sentieristica Family',
    #                'Progetti di abbattimento delle barriere architettoniche, segnalazione grado di accessibilitа']
user_inputs = []

while True:
    entry = input("Azione da visualizzare (scrivi 'END' per terminare la lista): ")
    if entry.strip() == "END":
        break
    user_inputs.append(entry.strip())

print("Voci inserite:", user_inputs)
    
choices = tassonomia.azione
choices = tassonomia.azione

    # identificazione degli input tra le scelte possibili
if len(user_inputs) > 1:
    azione = [process.extract(a, choices)[0][0] for a in user_inputs ]
elif len(user_inputs): 
    azione = [process.extract(user_inputs[0], choices)[0][0]]

    # preparazione dati per la visualizzazione
def wrapper(text, words_per_line=3):    
    words = text.replace('/',' - ').split()
    lines_per_chunk = words_per_line%len(words) + 1  
    lines = [' '.join(words[i:i+words_per_line]) for i in range(0, len(words), words_per_line)]    
    chunks = ['<br>'.join(lines[i:i+lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]    
    return chunks[0]
    
storia = pd.DataFrame(columns=['anno_compilazione'])
for a in azione:
    t = piani_comunali[piani_comunali.azione == a]
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
# Azioni simili ma categorizzate con diverse voci  (28.97s)
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
summary.sort_values(by='Frequenza',ascending=False).to_csv(f'{fp}azioni_diversimili.csv')
print(f'Tabella di azioni somiglianti ma che hanno diverse voci nella tassonomia salvata in {fp}azioni_diversimili.csv')
print(summary.head())