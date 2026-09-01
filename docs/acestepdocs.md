# Parâmetros POST /query_result
 - task_id_list: string[]
---
---
# Parâmetros POST /release_task
## BÁSICOS
 - prompt: String
 - vocal_language: String
 - lyrics: String
 - thinking: Boolean
 - audio_format: String
---
## DESCRIÇÃO
 - sample_mode: bool
 - sample_query: string
 - use_format: bool
---
## MODELO
 - model: string
---
## ATRIBUTOS DA MÚSICA
 - bpm: int
 - key_scale: string
 - time_signature: string
 - audio_duration: float
---
## TOKENS SEMÂNTICOS
 - audio_code_string: string or string[]
---
## CONTROLE DE GERAÇÃO
 - inference_steps: int
 - guidance_scale: float
 - use_random_seed: bool
 - seed: int
 - batch_size: int
---
## DiT
 - shift: float
 - infer_method: string
 - timesteps: string
 - use_adg: bool
 - cfg_interval_start: float
 - cfg_interval_end: float
 ---
 ## ARQUIVO DE REFERÊNCIA
 - reference_audio_path string
 - src_audio_path string
 - task_type string
 - instruction string
 - repainting_start float
 - repainting_end float
 - chunk_mask_mode string
 - audio_cover_strength float
 ---
 ## UPLOAD DE ARQUIVO DE REFERÊNCIA
 - reference_audio or red_audio: file
 - src_audio or ctx_audio: file
 ---
 ---
 

 
