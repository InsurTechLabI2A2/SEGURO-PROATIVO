"""
Agente 1 - Coletor: consome API publica OpenWeatherMap.
Requisito: Consumir dados provenientes de pelo menos uma API publica meteorologica.

Correcao de inconsistencia: a versao anterior usava um UNICO payload de MOCK fixo
(sempre com tempestade + calor + geada + seca simultaneos) para qualquer cidade
sem chave de API configurada. Isso fazia todas as cidades monitoradas dispararem
o mesmo conjunto de ~11 eventos a cada execucao, o que nao demonstra o requisito
de "mensagens personalizadas para diferentes perfis de segurados". Agora cada
cidade monitorada tem um cenario climatico proprio e plausivel, e o historico
(historico.py) e alimentado com leituras de "aquecimento" para que indicadores
acumulados (chuva 24h/72h, variacao de pressao, dias consecutivos) tambem sejam
demonstraveis logo na primeira execucao.
"""
import os
import requests
from dotenv import load_dotenv

import historico

load_dotenv()

API_KEY = os.getenv("OWM_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ---------------------------------------------------------------------------
# Cenarios simulados por cidade (usados quando nao ha OWM_API_KEY valida, ou
# quando a chamada real falha). Cada cenario foi escolhido para representar um
# risco climatico tipico da regiao, permitindo demonstrar eventos diferentes
# para cidades diferentes.
# ---------------------------------------------------------------------------
MOCKS_POR_CIDADE = {
    "Porto Alegre": {
        "name": "Porto Alegre",
        "main": {"temp": 22, "temp_min": 19, "temp_max": 24, "humidity": 82, "pressure": 1003},
        "wind": {"speed": 9, "gust": 14},
        "visibility": 7000,
        "rain": {"1h": 28, "3h": 54},
        "weather": [{"main": "Rain", "id": 502, "description": "chuva forte"}],
        "clouds": {"all": 90},
    },
    "Santos": {
        "name": "Santos",
        "main": {"temp": 26, "temp_min": 23, "temp_max": 28, "humidity": 81, "pressure": 1002},
        "wind": {"speed": 16, "gust": 23},
        "visibility": 8000,
        "rain": {"1h": 4, "3h": 9},
        "weather": [{"main": "Clouds", "id": 803, "description": "nublado com rajadas"}],
        "clouds": {"all": 75},
    },
    "Vacaria": {
        "name": "Vacaria",
        "main": {"temp": 7, "temp_min": 1, "temp_max": 13, "humidity": 58, "pressure": 1021},
        "wind": {"speed": 2, "gust": 4},
        "visibility": 10000,
        "rain": {"1h": 0, "3h": 0},
        "weather": [{"main": "Clear", "id": 800, "description": "ceu limpo"}],
        "clouds": {"all": 8},
    },
    "São Paulo": {
        "name": "São Paulo",
        "main": {"temp": 13, "temp_min": 11, "temp_max": 17, "humidity": 93, "pressure": 1016},
        "wind": {"speed": 2, "gust": 3},
        "visibility": 350,
        "rain": {"1h": 0, "3h": 1},
        "weather": [{"main": "Mist", "id": 701, "description": "neblina densa"}],
        "clouds": {"all": 95},
    },
    "Caxias do Sul": {
        "name": "Caxias do Sul",
        "main": {"temp": 15, "temp_min": 11, "temp_max": 18, "humidity": 72, "pressure": 1010},
        "wind": {"speed": 11, "gust": 15},
        "visibility": 5000,
        "rain": {"1h": 6, "3h": 14},
        "weather": [{"main": "Hail", "id": 906, "description": "granizo"}],
        "clouds": {"all": 85},
    },
    "Ribeirão Preto": {
        "name": "Ribeirão Preto",
        "main": {"temp": 39, "temp_min": 27, "temp_max": 41, "humidity": 16, "pressure": 1005},
        "wind": {"speed": 5, "gust": 8},
        "visibility": 10000,
        "rain": {"1h": 0, "3h": 0},
        "weather": [{"main": "Clear", "id": 800, "description": "sol forte"}],
        "clouds": {"all": 5},
        "uvi": 12,
    },
    "São Joaquim": {
        "name": "São Joaquim",
        "main": {"temp": -3, "temp_min": -4, "temp_max": 1, "humidity": 55, "pressure": 1023},
        "wind": {"speed": 6, "gust": 9},
        "visibility": 9000,
        "rain": {"1h": 0, "3h": 0},
        "weather": [{"main": "Snow", "id": 600, "description": "neve fraca"}],
        "clouds": {"all": 60},
    },
}

MOCK_PADRAO = {
    "name": "generico",
    "main": {"temp": 24, "temp_min": 18, "temp_max": 27, "humidity": 60, "pressure": 1013},
    "wind": {"speed": 4, "gust": 6},
    "visibility": 10000,
    "rain": {"1h": 0, "3h": 0},
    "weather": [{"main": "Clear", "id": 800, "description": "tempo estavel"}],
    "clouds": {"all": 20},
}

# Leituras sinteticas de "aquecimento" do historico (horas_atras, amostra), da
# mais antiga para a mais recente, para permitir demonstrar criterios
# acumulados (24h/72h/pressao/dias consecutivos) ja na primeira execucao.
SEED_HISTORICO_POR_CIDADE = {
    "Porto Alegre": [
        (22, {"temp": 21, "temp_min": 18, "temp_max": 23, "humidity": 80, "pressure": 1006, "rain_1h": 25}),
        (14, {"temp": 21, "temp_min": 18, "temp_max": 23, "humidity": 81, "pressure": 1005, "rain_1h": 22}),
        (5, {"temp": 22, "temp_min": 19, "temp_max": 24, "humidity": 83, "pressure": 1004, "rain_1h": 30}),
    ],
    "Santos": [
        (3.5, {"temp": 25, "temp_min": 23, "temp_max": 27, "humidity": 78, "pressure": 1013, "rain_1h": 2}),
    ],
    "São Paulo": [
        (30, {"temp": 12, "temp_min": 10, "temp_max": 16, "humidity": 94, "pressure": 1017, "rain_1h": 0}),
        (10, {"temp": 13, "temp_min": 11, "temp_max": 17, "humidity": 92, "pressure": 1016, "rain_1h": 0}),
    ],
    "Ribeirão Preto": [
        (480, {"temp": 38, "temp_min": 26, "temp_max": 40, "humidity": 18, "pressure": 1006, "rain_1h": 0}),
        (240, {"temp": 38, "temp_min": 26, "temp_max": 40, "humidity": 17, "pressure": 1005, "rain_1h": 0}),
        (26, {"temp": 38, "temp_min": 27, "temp_max": 40, "humidity": 16, "pressure": 1005, "rain_1h": 0}),
    ],
}


def coletar(cidade, pais="BR"):
    """Coleta dados atuais de uma cidade. Retorna JSON real da API ou MOCK especifico da cidade."""
    if cidade in SEED_HISTORICO_POR_CIDADE:
        historico.seed_historico(cidade, SEED_HISTORICO_POR_CIDADE[cidade])

    if not API_KEY:
        print(f"[COLETOR] Sem OWM_API_KEY configurada - usando MOCK de {cidade}")
        return dict(MOCKS_POR_CIDADE.get(cidade, MOCK_PADRAO))

    params = {"q": f"{cidade},{pais}", "appid": API_KEY, "units": "metric", "lang": "pt_br"}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[COLETOR] Erro consultando API real para {cidade}: {e} - usando MOCK")
        return dict(MOCKS_POR_CIDADE.get(cidade, MOCK_PADRAO))


if __name__ == "__main__":
    print(coletar("Porto Alegre"))
