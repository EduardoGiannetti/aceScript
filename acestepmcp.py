import os
from mcp.server.fastmcp import FastMCP
import requests
import json
import subprocess
from auto import DOWNLOAD_DIR, checar_status_musica, gerar_musica, BASE_URL

mcp = FastMCP("ACE-Step Music Generator")

@mcp.tool()
def gerar_musicas(tarefas: list[dict]) -> str:
    """
    IMPORTANTE - FLUXO DE EXECUÇÃO:
    1. Antes de chamar esta ferramenta, execute OBRIGATORIAMENTE a tool 'server_status' para verificar se o servidor ACE-Step está ativo.
    2. Se o servidor estiver offline, invoque 'awake_server' para iniciá-lo antes de tentar gerar a música.
    3. Realize todo o fluxo autonomamente a partir da ideia original do usuário, sem pedir confirmações intermediárias.

    PAPEL DE COMPILADOR (ESPECIALISTA EM COMENTÁRIOS CANTADOS):
    Você atua como compilador/prompt engineer do ACE-Step 1.5. Converta as ideias do usuário e os comentários de posts em um payload estruturado para a API.
    Não converta os comentários em uma outra letra com detalhes dos comentários, Ensira os comentários em si dentro da letra, adaptando-os para a estrutura mas contendo exatamente o texto inteiro do comentário.

    DIRETRIZES DE PROMPT E CAPTION (baseado no manual do ACE-Step):
    - 'prompt' / 'caption': Descreva o estilo geral, gênero, instrumentos, timbre vocal, textura e atmosfera (ex: "pop funk acelerado, vocais masculinos dinâmicos, síntese grave marcante, ritmo contagiante, produção limpa").
    - SEPARAÇÃO DE METADADOS: NÃO inclua BPM, tom (key) ou fórmula de compasso dentro do texto da 'caption/prompt'. Use exclusivamente os parâmetros dedicados ('bpm', 'key_scale', 'time_signature').
    - NÂO CONFLITE ELEMENTOS: Mantenha coerência entre o tom da legenda e o estilo musical desejado.

    REGRAS DE LETRA PARA COMENTÁRIOS CANTADOS ('lyrics'):
    - Adapte comentários de redes sociais em versos cantados, preservando a essência e o humor do comentário original, adaptando métricas para fluidez (6 a 10 sílabas por linha preferencialmente).
    - Use marcas de estrutura em colchetes para guiar a linha do tempo (ex: [Intro], [Verse], [Comment 1], [Chorus], [Outro]).
    - RÓTULOS CONCISOS: Pode usar tags compostas simples (ex: [Chorus - afiado] ou [Verse - falado]), mas EVITE empilhar muitas tags (ex: [Chorus - poderoso - harmonizado - agudo - épico]).
    - SEM INSTRUÇÕES DE PRODUÇÃO NO TEXTO: NUNCA coloque ruídos, direções de palco ou efeitos entre parênteses dentro do texto da letra (ex: NÃO use "(batida cai)" ou "(risos)"). Limite a letra apenas às palavras que devem ser efetivamente cantadas/faladas.
    - COERÊNCIA: Garanta que os instrumentos citados nas tags de estrutura da letra coincidam com o descrito na 'caption'.

    PARÂMETROS PADRÃO:
    - batch_size: Padrão 1 (use valores maiores até 8 apenas se o usuário solicitar variações/lotes).
    - model: Padrão "acestep-v15-turbo".
    - thinking: Padrão True (ativa a inferência CoT do LM interno para BPM e metadados).

    ESTRUTURA DE CADA ITEM NA LISTA 'tarefas':
    - prompt (str, obrigatório): Legenda rica de estilo/instrumentos (sem BPM/tom).
    - lyrics (str, opcional): Letra adaptada dos comentários com tags [Verse], [Chorus], etc.
    - bpm (int, opcional): Tempo musical em BPM (ex: 120).
    - key_scale (str, opcional): Tom/escala (ex: 'C Major', 'Am').
    - vocal_language (str, opcional): Idioma principal ('pt', 'en', etc.).
    - audio_duration (float, opcional): Duração total em segundos.
    - batch_size (int, opcional): Quantidade de variações (padrão 1).
    - model (str, opcional): Modelo DiT (padrão "acestep-v15-turbo").
    - thinking (bool, opcional): Ativa raciocínio CoT no LM (padrão True).
    - task_type (str, opcional): 'text2music', 'cover', 'repaint', etc.
    - reference_audio_path (str, opcional): Caminho absoluto de áudio de referência para estilo/timbre.
    - src_audio_path (str, opcional): Caminho absoluto de áudio de origem para cover ou edição local.    
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
    funcionando, rodando ou se deseja verificar a saúde do serviço. Se for retornado que o ace step
    está offline completamente, utilize a tool awake_server, para ligar o servidor
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
    
@mcp.tool()
def awake_server()-> str:
    """
    Roda o arquivo de inicialização do servidor da API do ace step caso ele esteja fora do ar,
    executando um comando no sistema em segundo plano, para rodar o arquivo .bat ou .sh se for linux/mac,
    com o caminho absoluto do arquivo.
    """
    COMANDO = r"C:\Users\EduardoGiannetti\Downloads\ACE-Step\start_api_server.bat"
    if not os.path.exists(COMANDO):
        return f"O arquivo de inicialização não foi encontrado"
    try:
        if os.name == 'nt':
            subprocess.Popen(f'start cmd /k "{COMANDO}"', shell=True)
        else:
            subprocess.Popen(["x-terminal-emulator", "-e", COMANDO])
        
        return "Nova janela de terminal aberta com sucesso. Acompanhe os logs da API diretamente na janela do prompt."
    except Exception as e:
        return f"Erro ao tentar abrir o terminal com os logs: {str(e)}"
        
if __name__ == "__main__":
    mcp.run()