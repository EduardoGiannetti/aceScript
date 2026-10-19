import json
import os
import signal
import subprocess
import time
import requests

API_PORT = 8001
BASE_URL = f"http://localhost:{API_PORT}"
INTERVALO_POLLING = 60  # segundos entre consultas de status
TIMEOUT_GERACAO = 30 * 600000  # tempo máximo de espera pela geração (segundos)
ACESTEP_DIR = os.environ.get("ACESTEP_DIR", r"C:\Users\EduardoGiannetti\Downloads\ACE-Step")
DOWNLOAD_DIR = r"C:\Users\EduardoGiannetti\Downloads\mermaid\downloads"
REMOTION_DIR = r"C:\Users\EduardoGiannetti\Downloads\remotion\timestamps"

def salvar_metadados_musica(task_id: str, payload: dict):
    """
    Salva o payload gerado pelo Claude em um JSON para sincronização futura.
    """
    # Usa diretamente a letra enviada no campo "lyrics" do payload.
    texto_letra = payload.get("lyrics", "")
    
    # Transforma o bloco de texto em uma lista de linhas/comentários individuais
    lista_comentarios_usados = [linha.strip() for linha in texto_letra.split('\n') if linha.strip()]
    
    dados = {
        "task_id": task_id,
        "text": lista_comentarios_usados, 
        "payload_completo": payload
    }
    
    # Salva no mesmo diretório de downloads com o ID da tarefa
    caminho_arquivo = os.path.join(REMOTION_DIR, f"{task_id}_lyrics.json")
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        
    print(f"Metadados e comentários salvos em: {caminho_arquivo}")
    
def _pids_escutando_na_porta(porta: int) -> set:
    """Retorna os PIDs dos processos que estão escutando na porta informada."""
    pids = set()
    if os.name == "nt":
        saida = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
        for linha in saida.splitlines():
            partes = linha.split()
            if len(partes) >= 5 and partes[3].upper() == "LISTENING" and partes[1].endswith(f":{porta}"):
                pids.add(int(partes[4]))
    else:
        saida = subprocess.run(["lsof", "-nP", "-t", f"-iTCP:{porta}", "-sTCP:LISTEN"],
                               capture_output=True, text=True).stdout
        pids.update(int(pid) for pid in saida.split() if pid.isdigit())
    pids.discard(0)
    return pids


def _descendentes(pid: int) -> set:
    """Retorna recursivamente os PIDs filhos de um processo (Linux/macOS)."""
    filhos = set()
    saida = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout
    for filho in (int(p) for p in saida.split() if p.isdigit()):
        filhos.add(filho)
        filhos |= _descendentes(filho)
    return filhos


def _processo_vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _encerrar_servidor_linux(porta: int, timeout: float):
    pids = _pids_escutando_na_porta(porta)
    # Guarda a árvore de processos e os grupos antes de encerrar, pois o
    # close_api_server.sh só mata o PID que escuta na porta, deixando órfãos
    # os processos filhos (ex.: workers do LLM que seguram a VRAM).
    arvore = set(pids)
    grupos = set()
    for pid in pids:
        arvore |= _descendentes(pid)
        try:
            grupos.add(os.getpgid(pid))
        except OSError:
            pass
    grupos.discard(os.getpgrp())  # nunca sinalizar o grupo deste próprio processo

    script = os.path.join(ACESTEP_DIR, "close_api_server.sh")
    if os.path.exists(script):
        # --port: o padrão do script é 8002; --force: o processo iniciado via
        # "uv run acestep-api" não contém "uvicorn"/"acestep.api_server" na cmdline.
        resultado = subprocess.run(["bash", script, "--port", str(porta), "--force"],
                                   capture_output=True, text=True)
        print(resultado.stdout.strip() or resultado.stderr.strip())
    else:
        print(f"Script {script} não encontrado; encerrando processos diretamente.")
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

    # Equivalente ao Ctrl+C no terminal: SIGINT para todo o grupo do servidor.
    for pgid in grupos:
        try:
            os.killpg(pgid, signal.SIGINT)
        except OSError:
            pass

    limite = time.time() + timeout
    while time.time() < limite and any(_processo_vivo(p) for p in arvore):
        time.sleep(0.5)

    for pid in arvore:
        if _processo_vivo(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


def encerrar_servidor_acestep(porta: int = API_PORT, timeout: float = 15) -> bool:
    """
    Encerra a API do ACE-Step e todos os seus processos filhos, liberando a
    memória de GPU/RAM ocupada pelos modelos. No Windows mata a árvore de
    processos com taskkill; no Linux/macOS usa o close_api_server.sh do ACE-Step
    e garante o encerramento dos processos filhos restantes.
    Retorna True se nada mais estiver escutando na porta ao final.
    """
    pids = _pids_escutando_na_porta(porta)
    if not pids:
        print("Servidor ACE-Step já não está em execução.")
        return True

    print(f"Encerrando servidor ACE-Step (PID(s) {', '.join(map(str, pids))})...")
    if os.name == "nt":
        for pid in pids:
            # /T encerra a árvore de processos, /F força o encerramento
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        _encerrar_servidor_linux(porta, timeout)

    limite = time.time() + timeout
    while time.time() < limite:
        if not _pids_escutando_na_porta(porta):
            print("Servidor ACE-Step encerrado e recursos liberados.")
            return True
        time.sleep(1)

    print("Não foi possível confirmar o encerramento do servidor ACE-Step.")
    return False


def gerar_musica(payload: dict, file_paths: dict = None, encerrar_servidor: bool = True):
    return gerar_e_baixar_musica(payload=payload, file_paths=file_paths, encerrar_servidor=encerrar_servidor)


def gerar_e_baixar_musica(payload: dict, file_paths: dict = None, encerrar_servidor: bool = True):
    """
    Cria a tarefa de geração, aguarda a conclusão, baixa o(s) áudio(s) e, por fim,
    encerra a API do ACE-Step para liberar os recursos (se encerrar_servidor=True).
    Retorna (task_id, lista_de_caminhos_baixados).
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Criando tarefa com payload: {payload}")

    try:
        task_id = _criar_tarefa(payload, file_paths)
        caminhos = _aguardar_e_baixar(task_id)
        print(f"Áudio(s) salvo(s) em: {', '.join(caminhos)}")
        return task_id, caminhos
    finally:
        if encerrar_servidor:
            encerrar_servidor_acestep()


def _criar_tarefa(payload: dict, file_paths: dict = None) -> str:
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
        salvar_metadados_musica(task_id, payload)
        return task_id
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        raise e


def _consultar_tarefa(task_id: str) -> dict:
    response = requests.post(f"{BASE_URL}/query_result", json={"task_id_list": [task_id]})
    response.raise_for_status()
    return response.json()["data"][0]


def _baixar_audios(task_id: str, job_data: dict) -> list:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
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

    return caminhos


def _aguardar_e_baixar(task_id: str) -> list:
    limite = time.time() + TIMEOUT_GERACAO
    while time.time() < limite:
        job_data = _consultar_tarefa(task_id)
        status = job_data["status"]
        if status == 1:
            return _baixar_audios(task_id, job_data)
        if status == 2:
            raise RuntimeError(f"Falha na geração do áudio no servidor (tarefa {task_id}).")
        print("Gerando... aguardando conclusão da tarefa.")
        time.sleep(INTERVALO_POLLING)
    raise TimeoutError(f"Tempo limite excedido aguardando a tarefa {task_id}.")


def checar_status_musica(task_id: str) -> str:
    try:
        job_data = _consultar_tarefa(task_id)
        status = job_data["status"]

        if status == 0:
            return "Status: Gerando... A tarefa ainda está em andamento."
        if status == 2:
            return "Falha na geração do áudio no servidor."
        if status == 1:
            caminhos = _baixar_audios(task_id, job_data)
            return f"Sucesso! Áudio(s) gerado(s) e salvo(s) em: {', '.join(caminhos)}"

        return f"Status desconhecido: {status}"
    except Exception as e:
        return f"Erro ao verificar status: {e}"