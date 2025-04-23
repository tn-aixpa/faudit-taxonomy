# P1-SuggerimentoModificheTassonomia

Specifiche e contesto:
- ```tipologia```: product-template
- ```ai```: NLP
-  ```dominio```: PA

Implementazione di statistiche descrittive per facilitare processi decisionali sulle tassonomie di progetti Family in Italia e Family Audit. 
Il codice è pensato per simulare un'interazione con i dati tramite linea di comando per facilitare l'adattamento a front end / interfaccia.

I due script ```SuggerimentiComuni.py``` e ```SuggerimentiAziende.py``` forniscono automaticamente le seguenti statistiche riguardanti i piani dei rispettivi domini:

- Voci della tassonomia meno utilizzate dai Comuni o dalle Organizzazioni coinvolte
- Voci della tassonomia meno utilizzate da un Comune o da una Organizzazione specifica
- Andamento storico della frequenza di voci della tassonomia scelte arbitrariamente
- Identificazione e creazione di dati riassuntivi che identificano voci della tassonomia **diverse** utilizzate in maniera equivalente.

### Esempi di dati, input e output
I dati sono disponibili nella cartella [data](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/). 
All'interno delle cartelle [outputComuni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputComuni) e [outputOrganizzazioni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputOrganizzazioni) è possibile visualizzare l'output previsto dallo script. 

Attualmente durante l'esecuzione del codice si richiedono i seguenti input che variano in base alla disponibilità nei dati. L'input viene automaticamente ricollegato alle possibili scelte di variabili nel dataset tramite la libreria ```fuzzywuzzy```.

#### Codice per suggerimenti ai Comuni:
|Ordine di apparizione della richiesta|Natura dell'input|Tipo di formato dell'input|Example|
| -|---|---|---|
|1|Soglia massima di frequenza delle azioni da considerare (per visualizzare le azioni usate meno frequentemente della soglia impostata)|numero intero|60|
|2|Nome della Provincia da analizzare|testo|"Trento"|
|3|Azione / azioni da considerare per analizzare la serie storica di uso nei dati|testo|"Sentieristica", "Agevolazioni tariffarie"|

Infine, viene prodotto un dataset che contiene la similarità tra ogni azione e tutte le altre azioni. Solo le similarità sopra una soglia del 75% (modificabile) vengono effettivamente salvate. La similarità è calcolata sui **titoli** identici o simili che il Comune ha fornito a due azioni, pur indicando due categorie della tassonomia differenti in esse. 

#### Codice per suggerimenti alle Organizzazioni:
|Ordine di apparizione della richiesta|Natura dell'input|Tipo di formato dell'input|Example|
| -|---|---|---|
|1|Soglia massima di frequenza delle azioni da considerare (per visualizzare le azioni usate meno frequentemente della soglia impostata)|numero intero|60|
|2|ID dell'Organizzazione da considerare per visualizzarne la frequenza delle azioni|numero intero|"12345055" o anche solo "5055"|
|3|ID della tassonomia del Family Audit per analizzare la serie storica di uso nei dati|numero intero|"11630707"|

Anche in questo caso, viene prodotto un dataset che contiene la similarità tra un'azione con ogni altra azione, salvate solo se oltre una soglia della similarità del 75%. La similarità è calcolata sulle **descrizioni** che un'azienda ha fornito a due azioni, pur indicando due categorie della tassonomia differenti in esse. I titoli non erano sufficientemente informativi, a differenza dei comuni. 


## Come eseguire il codice: 
- Prima di eseguire il codice, assicurarsi di aver installato le versioni compatibili di Python e delle sue dipendenze in [requisiti](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/blob/main/requirements.txt). 
- Nella posizione desiderata, aprire il terminale ed eseguire il download della repo:
```gh repo clone FluveFV/P1-SuggerimentoModificheTassonomia```
- Di seguito, utilizzare python per eseguire il singolo script, ad es. :
```python SuggerimentiComuni.py```
- Seguire le istruzioni sullo schermo in contemporanea alla lettura del codice per simulare un'interazione da linea di comando con i dati. Il codice è stato commentato appositamente. Assicurarsi di stare inserendo valori numerici quando esplicitamente richiesti e valori categoriali quando esplicitamente richiesti. 

--- 
🇺🇸-🏴󠁧󠁢󠁥󠁮󠁧󠁿 ENGLISH

Specifics:
- ```kind```: product-template
- ```ai```: NLP
-  ```domain```: PA

Statistical tools for facilitation of policy making processes on the taxonomies regarding Family in Italia and Family Audit projects.
The code has been built to simulate an interaction with data trough command line to facilitate a front-end adaptation.
Il codice è pensato per simulare un'interazione con i dati tramite linea di comando per facilitare un adattamento per interfaccia web.

The two scripts ```SuggerimentiComuni.py``` and ```SuggerimentiAziende.py``` yield automatically the following statistics and data regarding the plans of each domain:

- Categories less used by all Municipalities or all Organizations involved
- Categories less used by a Municipaliti or an Organization
- Time series for arbitrarily chosen categories
- Identification and production of summary dat that match different categories of the taxonomy based on how equivalently they are used, based on their description by the Municipality or organization. 

### Examples of data, input and output
The input data is available in [data](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/). 
Within each of the folders  [outputComuni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputComuni) and [outputOrganizzazioni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputOrganizzazioni) it is possible to see what is expected from the code. 

Currently, the code requires the following input that vary on the input data during execution.The input is automatically reconnected to the possible choices of variables in the dataset using the ```fuzzywuzzy``` package.
#### Code for advising Municipalities:
|Order of request display|Input's nature|Data type of input|Example|
|---|---|---|---|
|1|Upper threshold of frequency for actions to be considered (to visualize the actions used less frequently than the threshold)|integer|60|
|2|Name of the Province to analyze|string|"Trento"|
|3|Action / actions to consider for the analysis of their temporal series|string|("Sentieristica", "Agevolazioni tariffarie")|

Ultimately, a dataset containing the similarities between each action and the remaining actions is produced. Only the similarity above a (modifiable) 75% threshold are saved. The similarity is computed on similar or identical **titles** that a Municipality has given to two actions that have different categories in the taxonomy.

#### Code for advising companies:
|Order of request display|Input's nature|Data type of input|Example|
| -|---|---|---|
|1|Upper threshold of frequency for actions to be considered (to visualize the actions used less frequently than the threshold)|integer|60|
|2|ID of the Organization to consider to visualize the frequency of all the actions|integer|"12345055" or even just "5055"|
|3|ID of the taxonomy in Family Audit to analyze its time series of usage in the data|integer|"11630707"|

Even in this scenario, a dataset is produced containing the similarities between each action and the remaining actions. Only the similarity above a (modifiable) 75% threshold are saved. The similarity is computed on the identical or similar **descriptions** that a company provided to two actions, even though giving them two different taxonomical categories. Titles were not as informative as in Municipalities' data.

## How to execute code:
- Before executing code, ensure to install all compatible Python version and its dependencies through [requirements](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/blob/main/requirements.txt). 
- Open the terminal in the desired location and execute the download of the repo:
```gh repo clone FluveFV/P1-SuggerimentoModificheTassonomia```
- Then, use python to execute the individual script, i.e. :
```python SuggerimentiComuni.py```
- Follow the instructions on the screen (which will be in Italian) to simulate an interaction by command line with data. I advise to also look at the commented code in the meantime, ensuring to insert numerical values when explicitly requested.  Otherwise, ensure inserting categorical values when explicitly requested.

  
--- 

 ![newplot(6)](https://github.com/user-attachments/assets/640d4637-23e1-4b0d-9ba2-6ebcb5a5ac9b)

