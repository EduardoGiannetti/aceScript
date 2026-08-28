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
        # Se houver arquivos (como reference_audio ou src_audio), usamos data + files para multipart/form-data
        if file_paths and any(file_paths.values()):
            files = {}
            for key, path in file_paths.items():
                if path and os.path.exists(path):
                    files[key] = open(path, "rb")
            
            response = requests.post(f"{BASE_URL}/release_task", data=payload, files=files)
            
            # Fechar os arquivos após a requisição
            for f in files.values():
                f.close()
        else:
            # Requisicao padrao via JSON
            response = requests.post(f"{BASE_URL}/release_task", json=payload)
            
        response.raise_for_status()
        data = response.json().get("data", {})
        task_id = data.get("task_id")
        print(f"Tarefa criada! ID: {task_id}")
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        return

    # Polling no /query_result (checar a cada 5-10 segundos recomendado em vez de 60s)
    while True:
        time.sleep(90)
        try:
            query_res = requests.post(f"{BASE_URL}/query_result", json={"task_id_list": [task_id]})
            query_res.raise_for_status()
            job_data = query_res.json()["data"][0]
            status = job_data["status"]

            if status == 0:
                print("Status: Gerando...") # O status 0 significa que a tarefa está na fila ou em progresso
            elif status == 2:
                print("Falha na geração do áudio no servidor.") # O status 2 significa que a geração falhou
                break
            elif status == 1:
                print("Áudio gerado com sucesso!") # O status 1 significa que a geração foi concluída com sucesso[cite: 2]
                result_list = json.loads(job_data["result"])

                for index, item in enumerate(result_list):
                    audio_endpoint = item["file"]
                    download_url = f"{BASE_URL}{audio_endpoint}"
                    filename = f"musica_{task_id[:8]}_{index + 1}.mp3"
                    filepath = os.path.join(DOWNLOAD_DIR, filename)

                    audio_res = requests.get(download_url)
                    with open(filepath, "wb") as f:
                        f.write(audio_res.content)
                    print(f"Salvo em: {os.path.abspath(filepath)}")
                break
        except Exception as e:
            print(f"Erro durante a consulta: {e}")
            break