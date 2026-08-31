import json
import os
import time
import requests

BASE_URL = "http://localhost:8001"
DOWNLOAD_DIR = "./downloads"

def gerar_e_baixar_musica(payload: dict, file_paths: dict = None):
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Criando tarefa com payload: {payload}")

    try:
        if file_paths and any(file_paths.values()):
            files = {}
            for key, path in file_paths.items():
                if path and os.path.exists(path):
                    files[key] = open(path, "rb")
            
            response = requests.post(f"{BASE_URL}/release_task", data=payload, files=files)
            
            for f in files.values():
                f.close()
        else:
            response = requests.post(f"{BASE_URL}/release_task", json=payload)
            
        response.raise_for_status()
        data = response.json().get("data", {})
        task_id = data.get("task_id")
        print(f"Tarefa criada! ID: {task_id}")
        return task_id
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        raise e
        
def checar_status_musica(task_id: str) -> str:
    try:
            response = requests.post(f"{BASE_URL}/query_result", json={"task_id_list": [task_id]})
            response.raise_for_status()
            job_data = response.json()["data"][0]
            status = job_data["status"]
    
            if status == 0:
                return "Status: Gerando... A tarefa ainda está em andamento."
            elif status == 2:
                return "Falha na geração do áudio no servidor."
            elif status == 1:
                result_list = json.loads(job_data["result"])
                caminhos = []
                for index, item in enumerate(result_list):
                    download_url = f"{BASE_URL}{item['file']}"
                filename = f"musica_{task_id[:8]}_{index + 1}.mp3"
                filepath = os.path.join(DOWNLOAD_DIR, filename)

                audio_res = requests.get(download_url)
                with open(filepath, "wb") as f:
                    f.write(audio_res.content)
                caminhos.append(os.path.abspath(filepath))
            
            return f"Sucesso! Áudio(s) gerado(s) e salvo(s) em: {', '.join(caminhos)}"
    except Exception as e:
        return f"Erro ao verificar status: {e}"