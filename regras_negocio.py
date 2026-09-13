"""
Agente 3 - Regras de Negocio: determina quais segurados devem receber notificacoes.
Requisito: Aplicar regras de decisao.

Correcao de inconsistencia: o caminho de mock_segurados.json era relativo ao
arquivo antigo na raiz do projeto; com a reorganizacao em data/, o caminho foi
atualizado. Tambem foi ajustado para consumir a saida enriquecida (dicts com
nome/impacto) que o Agente Analisador agora devolve.
"""
import json
from pathlib import Path

SEGURADOS_PATH = Path(__file__).parent / "data" / "mock_segurados.json"

with open(SEGURADOS_PATH, encoding="utf-8") as f:
    SEGURADOS = json.load(f)

# Matriz de decisao: evento -> produtos afetados
REGRAS = {
    "E01": ["Residencial", "Empresarial"],
    "E02": ["Auto", "Frota", "Residencial"],
    "E03": ["Empresarial", "Residencial", "Frota"],
    "E04": ["Empresarial"],
    "E05": ["Vida", "Residencial", "Empresarial"],
    "E06": ["Rural"],
    "E07": ["Transporte", "Auto", "Frota"],
    "E08": ["Vida", "Residencial"],
    "E09": ["Residencial", "Empresarial"],
    "E10": ["Residencial", "Empresarial", "Rural"],
    "E11": ["Rural"],
    "E12": ["Empresarial"],
    "E13": ["Drones", "Aeronáutico"],
    "E14": ["Empresarial"],
    "E15": ["Aeronáutico", "Transporte"],
    "E16": ["Empresarial", "Residencial"],
    "E17": ["Frota", "Transporte"],
    "E18": ["Vida"],
    "E19": ["Rural", "Vida"],
    "E20": ["Transporte", "Empresarial"],
}


def aplicar_regras(eventos_detectados, cidade):
    """
    Filtra segurados da cidade cujo produto esta na regra do evento.
    `eventos_detectados` e a lista de dicts devolvida por analisar_eventos
    (cada item com "evento_id", "nome", "impacto").
    """
    notificacoes = []
    for evento in eventos_detectados:
        evento_id = evento["evento_id"]
        produtos_alvo = REGRAS.get(evento_id, [])
        for seg in SEGURADOS:
            if seg["cidade"] == cidade and seg["produto"] in produtos_alvo:
                notificacoes.append({
                    "evento_id": evento_id,
                    "evento_nome": evento.get("nome", evento_id),
                    "evento_impacto": evento.get("impacto", ""),
                    "segurado": seg,
                    "cidade": cidade,
                })
    return notificacoes


if __name__ == "__main__":
    exemplo_eventos = [{"evento_id": "E01", "nome": "CHUVA_INTENSA_RESIDENCIAL", "impacto": "teste"}]
    print(aplicar_regras(exemplo_eventos, "Porto Alegre"))
