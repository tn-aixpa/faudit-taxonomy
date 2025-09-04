import nuclio_sdk

import json
import pandas as pd
import numpy as np

def init(context):
    azioni_frequenza = context.project.get_dataitem("tassonomia_comuni_azioni_frequenza").as_df()
    azioni_unire = context.project.get_dataitem("tassonomia_comuni_azioni_unire").as_df()
    
    setattr(context, "azioni_frequenza", azioni_frequenza)
    setattr(context, "azioni_unire", azioni_unire)

def serve(context, event):

    context.logger.info(f"Received event: {event}")
    path = event.path

    if "to_delete" in path:
        soglia = int(event.fields["frequency_threshold"]) if "frequency_threshold" in event.fields else 3
        tassonomia = context.azioni_frequenza
        azioni_eliminare = tassonomia[tassonomia['Frequenza delle azioni'] <= soglia].rename(columns={'Frequenza delle azioni': 'frequency', 'ID_tassonomia': 'id'})[['id', 'frequency']]
        response = nuclio_sdk.Response()
        response.status_code = 200
        response.body = azioni_eliminare.to_dict("records")
        response.content_type='application/json'
        return response

    if "to_split" in path:
        soglia = int(event.fields["frequency_threshold"]) if "frequency_threshold" in event.fields else 100
        tassonomia = context.azioni_frequenza
        azioni_dividere = tassonomia[tassonomia['Frequenza delle azioni'] >= soglia].rename(columns={'Frequenza delle azioni': 'frequency', 'ID_tassonomia': 'id'})[['id', 'frequency']]
        response = nuclio_sdk.Response()
        response.status_code = 200
        response.body = azioni_dividere.to_dict("records")
        response.content_type='application/json'
        return response

    if "to_merge" in path:
        summary = context.azioni_unire.rename(columns={'ID_tassonomia_1': 'id1', 'ID_tassonomia_2': 'id2', 'titoli_1_list': 'actions1', 'titoli_2_list': 'actions2', 'Percentuale_di_similarità': 'similarity'})[['id1', 'id2', 'actions1', 'actions2', 'similarity']]
        response = nuclio_sdk.Response()
        response.status_code = 200
        response.body = summary.to_dict("records")
        response.content_type='application/json'
        return response
        
        
