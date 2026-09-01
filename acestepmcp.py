import os
from mcp.server.fastmcp import FastMCP
import requests
import json
from auto import DOWNLOAD_DIR, checar_status_musica, gerar_musica, BASE_URL

mcp = FastMCP("ACE-Step Music Generator")

@mcp.tool()
def gerar_musicas(tarefas: list[dict]) -> str:
    """
    Gera uma ou mais músicas no ACE-Step com base nas tarefas enviadas.
    Antes de chamar a ferramenta do ace step, faça a conversão da requisição da música para o formato ace step,
    Atue como compilador do ACE-Step. Sempre converta minhas ideias nos parâmetros estritos antes de executar a API. 
    O formato usado no payload é um dicionário com os parâmetros necessários. Exemplos de parâmetros que podem ser incluídos no dicionário do payload:
    
    "tags": lista de tags separadas por vírgula (light instrumental jazz, smooth jazz, soft piano, mellow saxophone, warm upright bass, brushed drums, relaxing cafe jazz, gentle swing rhythm, cozy and elegant mood, no vocals, clean and balanced mix).
    "lyrics": Texto estruturado usando seções entre colchetes ([intro], [verse], [chorus], [bridge], [outro] e [instrumental] ou [inst]).

    Cada item da lista 'tarefas' pode conter os parâmetros da API:
    - prompt (str, obrigatório): Descrição textual do estilo musical.
    - sample_query (str, opcional): Descrição em linguagem natural para guiar a geração de uma amostra (ex: "a soft Bengali love song").
    - lyrics (str, opcional): Letra da música.
    - audio_duration (float, opcional): Duração em segundos (ex: 60).
    - audio_format (str, opcional): Define o formato do áudio ('mp3', 'wav', etc.). Default é 'mp3'.
    - batch_size (int, opcional): Quantidade de gerações simultâneas em lote, com o limite máximo de 8.
    - reference_audio_path (string, opcional): Caminho absoluto no servidor para o áudio de referência a ser usado para transferência de estilo.
    - src_audio_path (string, opcional): Caminho absoluto no servidor para o áudio de origem para tarefas de repintura (repainting) ou cover.
    - repainting_start (float, opcional): Determina o tempo inicial (em segundos) para começar uma repintura no áudio de origem.
    - repainting_end (float, opcional): Determina o tempo final (em segundos) da repintura no áudio; o valor -1 processa até o final da faixa.
    - audio_cover_strength (float, opcional): Define a força das alterações de cover (0.0 a 1.0); valores menores (como 0.2) são indicados para transferências sutis de estilo.
    - reference_audio / ref_audio (file, opcional): Permite enviar/fazer upload do seu arquivo de áudio local como referência.
    - src_audio / ctx_audio (file, opcional): Permite enviar/fazer upload do seu arquivo de áudio local como fonte (source/context). 
    - bpm (int, opcional): Tempo musical em BPM (30-300).
    - instruction (string, opcional): Instruções de edição a serem processadas; o sistema preenche automaticamente com base no task_type se deixado vazio.
    - key_scale (str, opcional): Tom/escala (ex: 'C Major', 'Am').
    - task_type (str, opcional): 'text2music', 'cover', 'repaint', etc.
    - reference_audio_path (str, opcional): Caminho local absoluto do arquivo de áudio de referência.
    - thinking (bool, opcional): Se True, ativa a LLM interna para gerar códigos semânticos.
    - vocal_language (str, opcional): Idioma da voz ou das letras ('en', 'pt', 'ja', etc.).
    - sample_mode (bool, opcional): Habilita o modo de geração de amostra aleatória, gerando automaticamente descrições, letras e metadados via modelo de linguagem.
    - use_format (bool, opcional): Utiliza o modelo de linguagem para aprimorar e formatar o prompt e as letras fornecidas pelo usuário.
    - model (str, opcional): Seleciona qual modelo DiT será utilizado (ex: "acestep-v15-turbo").
    - time_signature (str, opcional): Define a fórmula de compasso (ex: 2, 3, 4, 6 representam respectivamente 2/4, 3/4, 4/4, 6/8).
    - audio_code_string (str, str[], opcional): Tokens semânticos de áudio (5Hz) usados para o funcionamento do llm_dit.
    - inference_steps (int, opcional): Número de passos de inferência para a geração do áudio.    
    """
    resultados = []
    for i, item in enumerate(tarefas, 1):
        payload = item.copy()
        file_paths = {}

        ref_path = payload.pop("reference_audio_path", None)
        if ref_path and os.path.exists(ref_path):
            file_paths["reference_audio"] = ref_path
            if "task_type" not in payload:
                payload["task_type"] = "cover"

        task_id = gerar_musica(payload=payload, file_paths=file_paths)
        resultados.append(f"Tarefa {i} enviada com sucesso! ID: {task_id}. Use 'verificar_status_musica' para acompanhar.")

    return "\n".join(resultados)

@mcp.tool()
def verificar_status_musica(task_id: str) -> str:
    """
    Verifica o status de uma tarefa de geração de música no ACE-Step.
    Se estiver pronta, faz o download. Use passando o task_id obtido na ferramenta 'gerar_musicas'.
    """
    return checar_status_musica(task_id)

@mcp.tool()
def server_status ()-> str:
    """
    Verifica o status do servidor ACE-Step, se está ativo e respondendo corretamente.
    Chame essa função sempre que o usuário perguntar se o servidor está online, ou ativo,
    funcionando, rodando ou se deseja verificar a saúde do serviço.
    """
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        status_info = response.json()
        if status_info.get("status") == "ok":
            return f"Servidor ACE-Step está ativo. Status: {status_info}"
        else:
            return f"Servidor ACE-Step retornou status inesperado: {status_info}"
    except requests.RequestException as e:
        return f"Erro ao verificar o status do servidor: {e}"
if __name__ == "__main__":
    mcp.run()