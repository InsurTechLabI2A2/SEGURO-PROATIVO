"""
Agente auxiliar - Historico: mantem uma janela deslizante de leituras por cidade.

Por que este modulo existe (correcao de inconsistencia):
Varios criterios documentados em data/eventos_20.json dependem de acumulados ao
longo do tempo - chuva em 24h (E09) e 72h (E14), variacao de pressao em 3h
(E10/E20), ou "2 dias consecutivos" de calor extremo (E05). O endpoint gratuito
de "current weather" da OpenWeatherMap devolve apenas uma fotografia do momento,
sem essas janelas. Antes, o codigo aproximava esses criterios usando campos que
nao tinham relacao com o que estava documentado (ex.: E11 checava umidade e
temperatura instantaneas em vez de chuva acumulada em 30 dias). Este modulo
resolve isso guardando as leituras localmente e calculando os agregados reais.

Limitacao assumida e documentada no relatorio tecnico: por ser um MVP validado
em execucoes pontuais (nao um servico 24/7), o historico de 30 dias (E11) e de
48h (E16) e aproximado pelas leituras efetivamente coletadas ate o momento, e
nao por uma serie temporal historica completa - isso exigiria um banco de series
temporais e um agendador rodando continuamente, fora do escopo pedido no
Desafio 5 (MVP funcional).

Para que a primeira execucao ja demonstre os eventos acumulados (e nao apenas
os instantaneos), a funcao `seed_historico` cria, apenas quando ainda nao existe
historico para a cidade, leituras sinteticas com timestamps relativos ao
momento da execucao (ex.: "ha 26 horas"). Isso e feito de forma transparente e
e citado tanto no README quanto no log de execucao.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

HIST_FILE = Path(__file__).parent / "historico_clima.json"
MAX_AMOSTRAS_POR_CIDADE = 60


def _agora():
    return datetime.now(timezone.utc)


def _carregar():
    if HIST_FILE.exists():
        try:
            with open(HIST_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _salvar(historico):
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def _parse_ts(amostra):
    try:
        return datetime.fromisoformat(amostra["timestamp"])
    except (KeyError, ValueError, TypeError):
        return None


def seed_historico(cidade, perfil_seed):
    """
    Cria leituras sinteticas de 'aquecimento' para a cidade, apenas se ainda
    nao houver historico registrado. `perfil_seed` e uma lista de tuplas
    (horas_atras, amostra_dict) definida por cidade em coletor.py, alinhada ao
    cenario climatico tipico daquela regiao.
    """
    historico = _carregar()
    if historico.get(cidade):
        return  # ja existe historico real: nao sobrescreve

    agora = _agora()
    serie = []
    for horas_atras, amostra in perfil_seed:
        ts = agora - timedelta(hours=horas_atras)
        registro = dict(amostra)
        registro["timestamp"] = ts.isoformat()
        serie.append(registro)

    historico[cidade] = serie
    _salvar(historico)


def registrar_leitura(cidade, dados_api):
    """Adiciona a leitura atual ao historico da cidade e devolve a serie atualizada."""
    historico = _carregar()
    serie = historico.get(cidade, [])

    main = dados_api.get("main", {})
    amostra = {
        "timestamp": _agora().isoformat(),
        "temp": main.get("temp"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "rain_1h": dados_api.get("rain", {}).get("1h", 0),
    }
    serie.append(amostra)
    serie = serie[-MAX_AMOSTRAS_POR_CIDADE:]
    historico[cidade] = serie
    _salvar(historico)
    return serie


def rain_acumulada(serie, horas):
    """Soma a chuva (mm/1h) de todas as leituras dentro da janela de `horas`."""
    limite = _agora() - timedelta(hours=horas)
    total = 0.0
    for amostra in serie:
        ts = _parse_ts(amostra)
        if ts and ts >= limite:
            total += amostra.get("rain_1h") or 0
    return total


def temp_media(serie, horas=720):
    limite = _agora() - timedelta(hours=horas)
    valores = [a["temp"] for a in serie if _parse_ts(a) and _parse_ts(a) >= limite and a.get("temp") is not None]
    return sum(valores) / len(valores) if valores else 0


def variacao_pressao(serie, horas=3):
    """Diferenca entre a pressao de ~`horas` atras e a leitura mais recente (positivo = queda)."""
    if not serie:
        return 0
    limite = _agora() - timedelta(hours=horas)
    passadas = [a for a in serie if _parse_ts(a) and _parse_ts(a) <= limite and a.get("pressure") is not None]
    pressao_atual = serie[-1].get("pressure")
    if pressao_atual is None or not passadas:
        return 0
    pressao_passada = passadas[-1]["pressure"]
    return pressao_passada - pressao_atual


def umidade_alta_sustentada(serie, horas=48, limite_umidade=90):
    limite = _agora() - timedelta(hours=horas)
    janela = [a for a in serie if _parse_ts(a) and _parse_ts(a) >= limite]
    if not janela:
        return False
    return all((a.get("humidity") or 0) > limite_umidade for a in janela)


def dias_consecutivos_acima(serie, campo, limite_valor, n_amostras=2):
    if len(serie) < n_amostras:
        return False
    ultimas = serie[-n_amostras:]
    return all((a.get(campo) or 0) > limite_valor for a in ultimas)
