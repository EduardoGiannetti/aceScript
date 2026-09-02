import json
import os
import time
import requests

BASE_URL = "http://localhost:8001"
DOWNLOAD_DIR = r"C:\Users\EduardoGiannetti\Downloads\mermaid\downloads"


def gerar_musica(payload: dict, file_paths: dict = None):
    return gerar_e_baixar_musica(payload=payload, file_paths=file_paths)


def gerar_e_baixar_musica(payload: dict, file_paths: dict = None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Criando tarefa com payload: {payload}")

    try:
        files = {}
        if file_paths and any(file_paths.values()):
            for key, path in file_paths.items():
                if path and os.path.exists(path):
                    files[key] = open(path, "rb")

        try:
            if files:
                response = requests.post(f"{BASE_URL}/release_task", data=payload, files=files)
            else:
                response = requests.post(f"{BASE_URL}/release_task", json=payload)
        finally:
            for f in files.values():
                f.close()

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
        if status == 2:
            return "Falha na geração do áudio no servidor."
        if status == 1:
            result_list = json.loads(job_data["result"])
            caminhos = []

            for index, item in enumerate(result_list):
                download_url = f"{BASE_URL}{item['file']}"
                filename = f"musica_{task_id[:8]}_{index + 1}.mp3"
                filepath = os.path.join(DOWNLOAD_DIR, filename)

                audio_res = requests.get(download_url)
                audio_res.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(audio_res.content)
                caminhos.append(os.path.abspath(filepath))

            return f"Sucesso! Áudio(s) gerado(s) e salvo(s) em: {', '.join(caminhos)}"

        return f"Status desconhecido: {status}"
    except Exception as e:
        return f"Erro ao verificar status: {e}"
if __name__ == "__main__":
    # Exemplo de uso
    payload = {
    "prompt": "funny comedic Brazilian song, upbeat meme music, bouncy rhythm, acoustic guitar and silly synths, humorous and energetic mood",
    "tags": "comedy, funny, upbeat, bouncy, acoustic, humorous, meme, clear vocals, male vocalist",
    "referece_audio_path": r"C:\Users\EduardoGiannetti\Downloads\mermaid\downloads\lilbro.mp3",
    "lyrics": """
    [intro]
    (Batida cômica e animada)

    [verse]
    Lula sabe bem fazer isso
    Foi ele que vazou o GTA 6!

    [chorus]
    Ai depois lembra q tinha uma pasta de bitcoin no HD kkkkk
    Isso é só pra quem faz coisa errada na vida
    faz isso geralmente quem tem algo a esconder..

    [verse 2]
    Pra qual político vc trabalha?
    Isso se chama ser idiota. 
    Basta usar zero Fill!

    [bridge]
    Vai resolver porra nenhuma!
    Polícia tá na bota?

    [outro]
    Não era melhor tacar fogo ??
    """,
    "vocal_language": "pt",
    "task_type": "text2music",
    "audio_duration": 60,
    "batch_size": 2
}
    task_id = gerar_musica(payload)
    print(f"Tarefa enviada! ID: {task_id}")
