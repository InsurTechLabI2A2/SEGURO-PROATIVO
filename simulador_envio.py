"""
Agente 5 - Simulador de Envio: simula o envio das notificacoes.
Requisito: Simular o envio das notificacoes.

Correcoes de inconsistencia:
1. Este arquivo se chamava "Simulador-Envio.py" (com hifen e maiuscula), o que
   tornava `from simulador_envio import simular_envio` em main.py impossivel de
   resolver em qualquer sistema operacional (hifen nao e valido em nome de
   modulo Python). Renomeado para simulador_envio.py.
2. O caminho do log usava `Path(__file__).parent.parent`, escrevendo o CSV um
   nivel ACIMA da raiz do projeto. Corrigido para a raiz do projeto.
"""
import csv
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "log_envios.csv"


def simular_envio(notificacoes_com_mensagem):
    LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["data_hora", "evento_id", "evento_nome", "segurado_id", "nome", "produto", "cidade", "canal", "mensagem", "status"]
        )
        for item in notificacoes_com_mensagem:
            notif = item["notificacao"]
            seg = notif["segurado"]
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                notif["evento_id"],
                notif.get("evento_nome", ""),
                seg["id"],
                seg["nome"],
                seg["produto"],
                notif["cidade"],
                seg["canal"],
                item["mensagem"][:200],
                "ENVIADO_SIMULADO",
            ])

    print(f"[SIMULADOR] {len(notificacoes_com_mensagem)} mensagens logadas em {LOG_FILE}")
    return str(LOG_FILE)
