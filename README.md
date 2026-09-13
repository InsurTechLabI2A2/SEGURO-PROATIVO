# Desafio 5 \- Ferramenta Inteligente para Comunicação Proativa com o Segurado

Instituto de Inteligência Artificial Aplicada \- I2A2 Grupo \- InsurTechLab

## Objetivo

Desenvolver uma solução baseada em IA capaz de realizar comunicação proativa com segurados a partir da análise de eventos externos meteorológicos, demonstrando como agentes inteligentes podem agregar valor ao relacionamento entre seguradoras e segurados.

## Arquitetura multiagente

| Agente | Arquivo | Responsabilidade |
| :---- | :---- | :---- |
| 1\. Coletor | `coletor.py` | Consome a API pública OpenWeatherMap (ou usa mock realista por cidade quando não há chave configurada) |
| 2\. Analisador | `analisador.py` | Aplica os 20 critérios de `data/eventos_20.json` sobre a leitura atual e sobre o histórico da cidade |
| 3\. Regras de Negócio | `regras_negocio.py` | Decide quais segurados devem ser notificados, cruzando evento x produto x cidade |
| 4\. Comunicador | `comunicador.py` | Gera a mensagem final (LLM via OpenAI se configurado, ou template de fallback) |
| 5\. Simulador de Envio | `simulador_envio.py` | Registra o envio simulado em `log_envios.csv` |
| Auxiliar: Histórico | `historico.py` | Mantém uma janela deslizante de leituras por cidade, necessária para os critérios acumulados (chuva 24h/72h, variação de pressão, dias consecutivos) |

## Fluxo completo

Coleta (API/mock) → Analisador (20 critérios \+ histórico) → Regras de negócio

→ Comunicador (LLM/templates) → Simulador de envio (log\_envios.csv)

## Estrutura do repositório

SEGURO-PROATIVO/

├── main.py                \# Orquestra o fluxo completo

├── coletor.py              \# Agente 1

├── analisador.py            \# Agente 2

├── regras\_negocio.py         \# Agente 3

├── comunicador.py            \# Agente 4

├── simulador\_envio.py         \# Agente 5

├── historico.py             \# Agente auxiliar (janela deslizante por cidade)

├── data/

│   ├── eventos\_20.json       \# Catálogo dos 20 eventos e seus critérios técnicos

│   └── mock\_segurados.json    \# Base de segurados de demonstração

│   └── Log-Envios.csv

├── docs/

│   ├── Relatorio-Tecnico-V4 - Seguro_Proativo__MVP.pdf         

│   └── APRESENTAÇÃO - Seguro_Proativo__MVP.pdf

├── requirements.txt

├── .env.example

└── LICENSE

## Instalação e execução

git clone https://github.com/insurtechlabi2a2/SEGURO-PROATIVO 

cd SEGURO-PROATIVO

pip install \-r requirements.txt

cp .env.example .env

\# Edite o .env com sua chave OpenWeatherMap (gratuita em openweathermap.org)

\# Opcional: adicione OPENAI\_API\_KEY para geração de mensagens com LLM real

python main.py

Sem nenhuma chave configurada, o sistema roda imediatamente usando dados meteorológicos simulados (um cenário realista e **diferente por cidade**), o que já demonstra o fluxo completo, ponta a ponta, sem nenhuma configuração adicional. O script gera `log_envios.csv` com todas as comunicações simuladas.

Executar `python main.py` mais de uma vez faz o histórico (`historico_clima.json`, gerado localmente e ignorado pelo Git) acumular novas leituras; é esperado que novos eventos acumulados (ex.: E14 em Porto Alegre, quando a chuva das últimas 72h ultrapassa 120mm) passem a aparecer a partir da segunda ou terceira execução, simulando um monitoramento contínuo real.

## Catálogo de eventos monitorados

A fonte de verdade dos 20 eventos e seus critérios técnicos é [`data/eventos_20.json`](http://data/eventos_20.json); a tabela abaixo é um resumo.

| ID | Nome | Critério técnico |
| :---- | :---- | :---- |
| E01 | CHUVA\_INTENSA\_RESIDENCIAL | rain.3h \> 50mm OU rain.1h \> 30mm |
| E02 | GRANIZO\_AUTOMOVEL | weather.main \== Hail OU weather.id em \[511, 906\] |
| E03 | VENTO\_FORTE\_COSTEIRO\_EMPRESARIAL | wind.gust \> 20 m/s OU wind.speed \> 15 m/s |
| E04 | TEMPESTADE\_RAIOS\_EQUIPAMENTOS | weather.main \== Thunderstorm |
| E05 | ONDA\_CALOR\_SAUDE\_RESIDENCIAL | temp\_max \> 38°C por 2 dias consecutivos\* |
| E06 | GEADA\_RURAL | temp\_min \< 2°C E clouds \< 20% |
| E07 | NEVOEIRO\_DENSO\_TRANSPORTE | visibility \< 500m |
| E08 | BAIXA\_UMIDADE\_RESPIRATORIO | humidity \< 20% |
| E09 | INUNDACAO\_RIO\_RESIDENCIAL | rain.24h \> 100mm E pressure \< 1005 hPa\* |
| E10 | CICLONE\_VENDAVAL | wind.speed \> 25 m/s E queda de pressão \> 8hPa/3h\* |
| E11 | SECA\_PROLONGADA\_RURAL | rain.30d \< 10mm E temp média \> 30°C\* |
| E12 | CALOR\_EXTREMO\_DATACENTER | temp \> 40°C |
| E13 | VENTO\_LATERAL\_DRONE | wind.speed \> 10 m/s |
| E14 | CHUVA\_PERSISTENTE\_OBRA | rain.72h \> 120mm\* |
| E15 | NEVE\_AERONAUTICA | weather.main \== Snow |
| E16 | ALTA\_UMIDADE\_MOFO\_ESTOQUE | humidity \> 90% sustentada por 48h\* |
| E17 | TEMPESTADE\_AREIA\_FROTA | wind.gust \> 18 m/s E visibility \< 1000m E temp \> 32°C |
| E18 | FRIO\_INTENSO\_TRABALHADOR | temp\_min \< \-2°C |
| E19 | UV\_EXTREMO\_RURAL | uvi \> 11 |
| E20 | QUEDA\_PRESSAO\_LOGISTICA | queda de pressão \> 10hPa em 3h\* |

\* Critérios acumulados/temporais calculados pelo módulo `historico.py` (ver [Limitações conhecidas](#limitações-conhecidas)).

## Cenários de demonstração por cidade (modo mock)

| Cidade | Evento(s) principal(is) demonstrado(s) |
| :---- | :---- |
| Porto Alegre | E01 (chuva intensa) e E09 (inundação, via acumulado 24h) |
| Santos | E03 (vento costeiro) e E20 (queda de pressão em 3h) |
| Vacaria | E06 (geada rural) |
| São Paulo | E07 (nevoeiro denso) e E16 (umidade alta sustentada 48h) |
| Caxias do Sul | E02 (granizo) e E13 (vento lateral) |
| Ribeirão Preto | E05 (onda de calor, 2 dias), E08 (baixa umidade), E11 (seca prolongada) e E19 (UV extremo) |
| São Joaquim | E15 (neve) e E18 (frio intenso) |

## Requisitos atendidos

- [x] Consumir dados de API pública meteorológica (OpenWeatherMap)  
- [x] Identificar automaticamente eventos climáticos  
- [x] Aplicar regras de decisão (matriz evento x produto x cidade)  
- [x] Gerar mensagens personalizadas com IA (LLM opcional \+ fallback por template)  
- [x] Simular envio (log\_envios.csv)  
- [x] Demonstrar fluxo completo (`python main.py`, sem nenhuma chave obrigatória)

## Limitações conhecidas

- A API gratuita de "current weather" da OpenWeatherMap devolve apenas uma fotografia do momento. Critérios que dependem de janelas de tempo (chuva em 24h/72h/30 dias, variação de pressão em 3h, 2 dias consecutivos de calor, 48h de umidade alta) são aproximados por `historico.py`, que guarda as leituras localmente e calcula os agregados a partir delas. Isso é adequado para um MVP validado em execuções pontuais; um serviço contínuo em produção usaria uma série temporal real armazenada em banco de dados.  
- O evento E17 (tempestade de areia) é um cenário climático raro no Brasil; foi mantido no catálogo original a pedido do desafio, mas não é reforçado nos mocks de demonstração por não ser representativo do território nacional.  
- O indicador de UV (`uvi`) não está disponível no endpoint gratuito de "current weather"; nos mocks ele é simulado diretamente. Em uma integração real, seria necessário o endpoint "One Call" (camada paga) ou outra fonte.

## Licença

Este projeto está licenciado sob a licença MIT [http://LICENSE](https://github.com/InsurTechLabI2A2/SEGURO-PROATIVO/blob/main/LICENSE).  
