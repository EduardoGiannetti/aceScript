from auto import gerar_musica
if __name__ == "__main__":
    payload = {
        "prompt": "paródia de música meme brasileira, comentários de internet cantados, voz masculina dramática e satírica, violão acústico simples, tom cômico exagerado, estilo viral de comentários do YouTube.",
        "tags": "comedy, funny, orchestral, epic, acoustic, humorous, meme, clear vocals, male vocalist",
        "lyrics": """
        [verse]
        Esse cara sabe bem fazer isso, viu
        Foi ele que vazou o GTA 6
        Aí depois lembra que tinha uma pasta de bitcoin no HD
        isso é só pra quem faz coisa errada na vida

        [chorus]
        Faz isso geralmente quem tem algo a esconder
        Isso se chama ser idiota, basta usar zero fill
        Vai resolver porra nenhuma

        [bridge]
        Polícia tá na bota?
        Não era melhor tacar fogo?
        desse jeito aí nem a NASA recupera
        
        [outro]
        Pra qual político você trabalha?
        [instrumental]
        """,
        "vocal_language": "pt",
        #"task_type": "cover",
        #"audio_cover_strength": 0.5,
        "batch_size": 2
    }
    file_path = {
        "reference_audio": r"C:\Users\EduardoGiannetti\Downloads\ttk.mp3"
    }
    task_id = gerar_musica(payload, file_paths=file_path)
    print(f"Tarefa enviada! ID: {task_id}")