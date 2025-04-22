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

### Esempi di input e output
All'interno delle cartelle [outputComuni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputComuni) e [outputOrganizzazioni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputOrganizzazioni) è possibile visualizzare l'output previsto dallo script. 
I dati di input sono disponibili nella cartella [data](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/). 

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
- ```tipologia```: product-template
- ```ai```: NLP
-  ```dominio```: PA

Statistical tools for facilitation of policy making processes on the taxonomies regarding Family in Italia and Family Audit projects.
The code has been built to simulate an interaction with data trough command line to facilitate a front-end adaptation.
Il codice è pensato per simulare un'interazione con i dati tramite linea di comando per facilitare un adattamento per interfaccia web.

The two scripts ```SuggerimentiComuni.py``` and ```SuggerimentiAziende.py``` yield automatically the following statistics and data regarding the plans of each domain:

- Categories less used by all Municipalities or all Organizations involved
- Categories less used by a Municipaliti or an Organization
- Time series for arbitrarily chosen categories
- Identification and production of summary dat that match different categories of the taxonomy based on how equivalently they are used, based on their description by the Municipality or organization. 

### Examples of input and output
Within each of the folders  [outputComuni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputComuni) and [outputOrganizzazioni](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/outputOrganizzazioni) it is possible to see what is expected from the code. The input data is also available in [data](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/tree/main/). 

## How to execute code:
- Before executing code, ensure to install all compatible Python version and its dependencies through [requirements](https://github.com/FluveFV/P1-SuggerimentoModificheTassonomia/blob/main/requirements.txt). 
- Open the terminal in the desired location and execute the download of the repo:
```gh repo clone FluveFV/P1-SuggerimentoModificheTassonomia```
- Then, use python to execute the individual script, i.e. :
```python SuggerimentiComuni.py```
- Follow the instructions on the screen (which will be in Italian) to simulate an interaction by command line with data. I advise to also look at the commented code in the meantime, ensuring to insert numerical values when explicitly requested.  Otherwise, ensure inserting categorical values when explicitly requested.

  
--- 

 ![newplot(6)](https://github.com/user-attachments/assets/640d4637-23e1-4b0d-9ba2-6ebcb5a5ac9b)

