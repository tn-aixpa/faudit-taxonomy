import os
import pandas as pd
import numpy as np
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




    