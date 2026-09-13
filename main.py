"""
Fluxo completo da solucao - Desafio 5
1. Coleta -> 2. Identificacao -> 3. Regras -> 4. Geracao -> 5. Simulacao

Correcao de inconsistencia: os imports abaixo apontavam para "analisador" e
"simulador_envio" enquanto os arquivos reais no repositorio se chamavam
"Analisador.py" e "Simulador-Envio.py" - isso quebrava a execucao (o segundo
caso falha em qualquer sistema operacional, por causa do hifen). Os arquivos
foram renomeados e os imports abaixo agora resolvem corretamente.
"""
from coletor import coletar
from analisador import analisar_eventos
from regras_negocio import aplicar_regras
from comunicador import gerar_mensagem_ia
from simulador_envio import simular_envio

# Correcao de inconsistencia: "São Joaquim" existia em data/mock_segurados.json
# (segurado S10, produto Vida) mas nao estava nesta lista, entao nunca era
# monitorada e aquele segurado nunca podia receber notificacao. Adicionada.
CIDADES_MONITORADAS = [
    "Porto Alegre",
    "Santos",
    "Vacaria",
    "São Paulo",
    "Caxias do Sul",
    "Ribeirão Preto",
    "São Joaquim",
]


def executar_fluxo():
    todas_notificacoes = []

    for cidade in CIDADES_MONITORADAS:
        print(f"\n=== {cidade} ===")
        dados = coletar(cidade)

        eventos = analisar_eventos(dados, cidade)
        nomes_eventos = [e["evento_id"] for e in eventos]
        print(f"[ANALISADOR] Eventos detectados: {nomes_eventos}")

        notificacoes = aplicar_regras(eventos, cidade)
        print(f"[REGRAS] Segurados a notificar: {len(notificacoes)}")

        for notif in notificacoes:
            msg = gerar_mensagem_ia(notif, dados)
            todas_notificacoes.append({"notificacao": notif, "mensagem": msg, "dados_api": dados})
            print(f"  -> {notif['evento_id']} -> {notif['segurado']['nome']} ({notif['segurado']['produto']}): {msg[:80]}...")

    log = simular_envio(todas_notificacoes)
    print(f"\nFluxo completo demonstrado. Total {len(todas_notificacoes)} comunicações proativas geradas.")
    print(f"Log: {log}")
    return todas_notificacoes


if __name__ == "__main__":
    executar_fluxo()
