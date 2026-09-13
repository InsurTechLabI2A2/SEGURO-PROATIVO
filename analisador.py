"""
Agente 2 - Analisador: identifica automaticamente eventos climaticos relevantes.
Requisito: Identificar automaticamente eventos climaticos relevantes.

Correcoes de inconsistencia aplicadas nesta versao:
1. Caminho do catalogo de eventos era ambiguo e nunca resolvia (procurava
   "eventos_20.json" enquanto o arquivo se chamava "Eventos-20.json"); a
   variavel resultante nem sequer era usada na deteccao. Agora ha um unico
   caminho canonico (data/eventos_20.json) e o catalogo E realmente usado
   para enriquecer cada evento detectado com nome/impacto de negocio.
2. Os limiares de E09, E11, E14 e E20 nao correspondiam ao criterio_tecnico
   documentado no catalogo (ex.: E11 checava umidade/temperatura instantaneas
   em vez de chuva acumulada em 30 dias). Foram reescritos para usar os
   agregados calculados pelo modulo historico.py, batendo com o documentado.
3. E05, E10 e E16 tambem dependiam de janelas de tempo (2 dias consecutivos,
   variacao de pressao em 3h, 48h de umidade alta) que a chamada unica de API
   nao fornece; agora usam o historico da propria cidade.
"""
import json
from pathlib import Path

import historico

EVENTOS_PATH = Path(__file__).parent / "data" / "eventos_20.json"


def carregar_catalogo_eventos():
    with open(EVENTOS_PATH, encoding="utf-8") as f:
        eventos = json.load(f)
    return {e["evento_id"]: e for e in eventos}


CATALOGO_EVENTOS = carregar_catalogo_eventos()


def analisar_eventos(dados_api, cidade):
    """
    Aplica os 20 criterios do catalogo (data/eventos_20.json) sobre a leitura
    atual da API (instantaneos) e sobre o historico da cidade (acumulados).
    Retorna uma lista de dicts: {"evento_id", "nome", "impacto"}.
    """
    serie = historico.registrar_leitura(cidade, dados_api)

    main = dados_api.get("main", {})
    wind = dados_api.get("wind", {})
    rain = dados_api.get("rain", {})
    clouds = dados_api.get("clouds", {})
    weather = dados_api.get("weather", [{}])[0]
    visibility = dados_api.get("visibility", 10000)

    temp = main.get("temp", 0)
    temp_min = main.get("temp_min", temp)
    temp_max = main.get("temp_max", temp)
    humidity = main.get("humidity", 50)
    pressure = main.get("pressure", 1013)
    clouds_pct = clouds.get("all", 50)
    wind_speed = wind.get("speed", 0)
    wind_gust = wind.get("gust", wind_speed)
    rain_1h = rain.get("1h", 0)
    rain_3h = rain.get("3h", rain_1h)
    weather_main = weather.get("main", "")
    weather_id = weather.get("id")
    uvi = dados_api.get("uvi", dados_api.get("current", {}).get("uvi", 0))

    rain_24h = historico.rain_acumulada(serie, 24)
    rain_72h = historico.rain_acumulada(serie, 72)
    rain_30d = historico.rain_acumulada(serie, 24 * 30)
    temp_media_30d = historico.temp_media(serie, 24 * 30)
    queda_pressao_3h = historico.variacao_pressao(serie, 3)
    calor_2_dias = historico.dias_consecutivos_acima(serie, "temp_max", 38, n_amostras=2)
    umidade_sustentada_48h = historico.umidade_alta_sustentada(serie, horas=48, limite_umidade=90)

    ids_detectados = []

    # E01 - CHUVA_INTENSA_RESIDENCIAL: rain.3h > 50mm OU rain.1h > 30mm
    if rain_3h > 50 or rain_1h > 30:
        ids_detectados.append("E01")

    # E02 - GRANIZO_AUTOMOVEL: weather.main == Hail OR weather.id in [511, 906]
    if weather_main == "Hail" or weather_id in [511, 906]:
        ids_detectados.append("E02")

    # E03 - VENTO_FORTE_COSTEIRO_EMPRESARIAL: wind.gust > 20 OU wind.speed > 15
    if wind_gust > 20 or wind_speed > 15:
        ids_detectados.append("E03")

    # E04 - TEMPESTADE_RAIOS_EQUIPAMENTOS: weather.main == Thunderstorm
    if weather_main == "Thunderstorm":
        ids_detectados.append("E04")

    # E05 - ONDA_CALOR_SAUDE_RESIDENCIAL: temp_max > 38 por 2 dias consecutivos
    if calor_2_dias:
        ids_detectados.append("E05")

    # E06 - GEADA_RURAL: temp_min < 2 AND clouds < 20%
    if temp_min < 2 and clouds_pct < 20:
        ids_detectados.append("E06")

    # E07 - NEVOEIRO_DENSO_TRANSPORTE: visibility < 500m
    if visibility < 500:
        ids_detectados.append("E07")

    # E08 - BAIXA_UMIDADE_RESPIRATORIO: humidity < 20%
    if humidity < 20:
        ids_detectados.append("E08")

    # E09 - INUNDACAO_RIO_RESIDENCIAL: rain.24h > 100mm AND pressure < 1005
    if rain_24h > 100 and pressure < 1005:
        ids_detectados.append("E09")

    # E10 - CICLONE_VENDAVAL: wind.speed > 25 AND queda de pressao > 8hPa/3h
    if wind_speed > 25 and queda_pressao_3h > 8:
        ids_detectados.append("E10")

    # E11 - SECA_PROLONGADA_RURAL: rain.30d < 10mm AND temp_media > 30
    if rain_30d < 10 and temp_media_30d > 30:
        ids_detectados.append("E11")

    # E12 - CALOR_EXTREMO_DATACENTER: temp > 40
    if temp > 40:
        ids_detectados.append("E12")

    # E13 - VENTO_LATERAL_DRONE: wind.speed > 10
    if wind_speed > 10:
        ids_detectados.append("E13")

    # E14 - CHUVA_PERSISTENTE_OBRA: rain.72h > 120mm
    if rain_72h > 120:
        ids_detectados.append("E14")

    # E15 - NEVE_AERONAUTICA: weather.main == Snow
    if weather_main == "Snow":
        ids_detectados.append("E15")

    # E16 - ALTA_UMIDADE_MOFO_ESTOQUE: humidity > 90% por 48h sustentada
    if umidade_sustentada_48h:
        ids_detectados.append("E16")

    # E17 - TEMPESTADE_AREIA_FROTA: wind.gust > 18 AND visibility < 1000 AND temp > 32
    if wind_gust > 18 and visibility < 1000 and temp > 32:
        ids_detectados.append("E17")

    # E18 - FRIO_INTENSO_TRABALHADOR: temp_min < -2
    if temp_min < -2:
        ids_detectados.append("E18")

    # E19 - UV_EXTREMO_RURAL: uvi > 11
    if uvi > 11:
        ids_detectados.append("E19")

    # E20 - QUEDA_PRESSAO_LOGISTICA: queda de pressao > 10hPa/3h
    if queda_pressao_3h > 10:
        ids_detectados.append("E20")

    ids_unicos = sorted(set(ids_detectados))
    return [
        {
            "evento_id": eid,
            "nome": CATALOGO_EVENTOS.get(eid, {}).get("nome", eid),
            "impacto": CATALOGO_EVENTOS.get(eid, {}).get("impacto", ""),
        }
        for eid in ids_unicos
    ]


if __name__ == "__main__":
    from coletor import coletar

    dados = coletar("Porto Alegre")
    print(analisar_eventos(dados, "Porto Alegre"))
