import json
import os
import time
import requests

# Configurações do Servidor
BASE_URL = "http://localhost:8001"
DOWNLOAD_DIR = "./downloads"


def gerar_e_baixar_musica(prompt: str):
    # 1. Garante que a pasta de download existe
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 2. Criar a tarefa no /release_task
    print("Criando tarefa de geração...")
    payload = {
        "prompt": prompt,
        "thinking": False,  # Desativado para não exigir LLM no servidor
        "use_format": False,  # Desativado para não exigir LLM no servidor
        "use_cot_caption": False,
        "use_cot_language": False,
        "audio_format": "mp3",
        "audio_duration": 60,
    }

    try:
        response = requests.post(f"{BASE_URL}/release_task", json=payload)
        response.raise_for_status()
        data = response.json()["data"]
        task_id = data["task_id"]
        print(f"Tarefa criada! ID: {task_id}")
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        return

    # 3. Polling no /query_result
    print("Processando áudio (checando a cada 5 segundos)...")
    while True:
        time.sleep(60)

        try:
            query_res = requests.post(
                f"{BASE_URL}/query_result", json={"task_id_list": [task_id]}
            )
            query_res.raise_for_status()

            job_data = query_res.json()["data"][0]
            status = job_data["status"]

            if status == 0:
                print("⏳ Status: Gerando...")
            elif status == 2:
                print("❌ Falha na geração do áudio no servidor.")
                break
            elif status == 1:
                print("🎉 Áudio gerado com sucesso!")

                # O campo 'result' vem como uma string JSON que precisa ser parseada
                result_list = json.loads(job_data["result"])

                # 4. Baixa todos os arquivos de áudio gerados na tarefa
                for index, item in enumerate(result_list):
                    audio_endpoint = item["file"]  # Rota /v1/audio?path=...
                    download_url = f"{BASE_URL}{audio_endpoint}"
                    filename = f"musica_{task_id[:8]}_{index + 1}.mp3"
                    filepath = os.path.join(DOWNLOAD_DIR, filename)

                    print(f"⬇Baixando: {filename}...")
                    audio_res = requests.get(download_url)
                    audio_res.raise_for_status()

                    with open(filepath, "wb") as f:
                        f.write(audio_res.content)

                    print(f"Salvo em: {os.path.abspath(filepath)}")

                break
        except Exception as e:
            print(f"⚠️ Erro durante a consulta: {e}")
            break


if __name__ == "__main__":
    PROMPT_TEXTO = "Make a lofi chill beat with a retro tone, with ethereal leads and synths in the background, and a smooth bassline"
    gerar_e_baixar_musica(PROMPT_TEXTO)