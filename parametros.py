tools = [
    {
        "type": "function",
        "function": {
            "name": "create_music_task",
            "description": "Cria uma ou mais músicas com base nas especificações do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Descrição musical do que deve ser gerado."
                    },
                    "lyrics": {
                        "type": "string",
                        "description": "Letra da música, se fornecida."
                    },
                    "thinking": {
                        "type": "boolean",
                        "description": "Ative como true para usar LLM para gerar tokens semânticos (melhor qualidade)."
                    },
                    "task_type": {
                        "type": "string",
                        "enum": ["text2music", "cover", "repaint", "lego", "extract", "complete"],
                        "description": "Tipo de tarefa. Use 'cover' ou 'repaint' se usar um áudio de referência."
                    },
                    "reference_audio_path": {
                        "type": "string",
                        "description": "Caminho local para o arquivo de áudio de referência no computador do usuário, se houver."
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]