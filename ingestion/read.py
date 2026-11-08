import gzip
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

"""  
in : data
out : list of rows
"""

def ingest(path:str):
    try :
        files=os.listdir(path)
        rows = []
        for file in files : 
            file_path = os.path.join(path,file)
            opener = gzip.open(file_path,mode='rt',encoding='utf-8') if file.endswith(".gz") else open(file_path,mode='r',encoding='utf-8')
            with opener as f :
                rows.extend(f.readlines())
        return rows

    except Exception as e:
        logger.error(f"Erreur pendant la lecture du dossier {path} : {e}")
        return
    return

if __name__ == "__main__" :
    data = ingest('./data')
    if (data):
        print(data)