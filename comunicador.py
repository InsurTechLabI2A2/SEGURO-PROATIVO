"""
Agente 4 - Comunicador: gera mensagens personalizadas utilizando IA.
Requisito: Gerar mensagens personalizadas utilizando Inteligencia Artificial ou
modelos de linguagem.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Templates base - fallback se sem LLM configurada
TEMPLATES = {
    "E01": "Olá {nome}, identificamos chuva intensa de {detalhe} em {cidade} nas próximas 3h. Para seu seguro {produto}: 1) Eleve móveis e eletrodomésticos 2) Desligue energia da área térrea. Estamos monitorando.",
    "E02": "{nome}, alerta de granizo em {cidade}. Seu seguro {produto} pode ser acionado por danos de granizo. Recomendamos recolher veículo para garagem coberta e evitar estacionar sob árvores.",
    "E03": "{nome} - {cidade}: ventos de {detalhe} previstos. Verifique fixação de telhas, placas e feche janelas do galpão. Risco de destelhamento.",
    "E04": "{nome}, tempestade com raios em {cidade}. Para evitar queima de equipamentos: desligue da tomada e use nobreak. Seu seguro empresarial cobre danos elétricos.",
    "E05": "Onda de calor de {detalhe} em {cidade}, já há 2 dias. {nome}, mantenha-se hidratado, evite exposição 11h-15h e não deixe aparelhos ligados sem supervisão.",
    "E06": "Geada prevista em {cidade}, {nome}. Proteja lavoura e recolha animais para galpão. Seu seguro rural cobre geada.",
    "E07": "Nevoeiro denso em {cidade} – visibilidade {detalhe}. {nome}, evite viajar à noite, use farol baixo e mantenha distância. Atraso de entrega pode ocorrer.",
    "E08": "Umidade baixa de {detalhe} em {cidade}. {nome}, beba água, umidifique ambiente e não queime lixo – risco de incêndio e crise respiratória.",
    "E09": "Alerta de inundação em {cidade}, {nome}. Chuva acumulada nas últimas 24h ultrapassou 100mm. Retire documentos e leve veículo para área alta.",
    "E10": "Ciclone/vendaval em {cidade} – ventos {detalhe} e queda brusca de pressão. {nome}, reforce telhas, retire objetos do quintal e feche comércio mais cedo.",
    "E11": "Seca prolongada em {cidade}, {nome}. Chuva acumulada no período está muito abaixo do normal. Avalie irrigação e contate seu corretor sobre cobertura de seca.",
    "E12": "Calor extremo {detalhe} em {cidade}, {nome}. Risco de falha de data center. Ligue refrigeração redundante – seu seguro cyber/equipamentos cobre.",
    "E13": "Vento lateral {detalhe} em {cidade}. {nome}, aborte voo de drone hoje – risco de queda. Seguro de drones acionável.",
    "E14": "Chuva persistente acumulada nas últimas 72h em {cidade}, {nome}. Verifique drenagem da obra e impermeabilização – evita infiltração.",
    "E15": "Neve em {cidade}, {nome}. Pista com gelo. Cancele decolagem – risco de gelo em asa. Contate seguro aeronáutico.",
    "E16": "Umidade acima de 90% sustentada nas últimas 48h em {cidade}, {nome}. Ligue desumidificador para proteger estoque contra mofo.",
    "E17": "Tempestade de areia em {cidade}, {nome}. Vento {detalhe} – troque filtro de ar da frota.",
    "E18": "Frio intenso {detalhe} em {cidade}, {nome}. Use EPI térmico – risco de hipotermia para trabalho externo.",
    "E19": "UV extremo em {cidade}, {nome}. Pausa de 11h-15h para trabalhador rural e proteja lavoura.",
    "E20": "Queda brusca de pressão (>10hPa em 3h) em {cidade}, {nome}. Tempestade severa iminente. Porto/logística pode fechar – carga com atraso.",
}


def gerar_mensagem_ia(notificacao, dados_api):
    """
    Tenta usar a OpenAI (se houver OPENAI_API_KEY configurada); caso contrário,
    ou se a chamada falhar, usa o template de fallback correspondente ao evento.
    """
    evento_id = notificacao["evento_id"]
    evento_nome = notificacao.get("evento_nome", evento_id)
    seg = notificacao["segurado"]
    cidade = notificacao["cidade"]
    detalhe = (
        f"{dados_api.get('main', {}).get('temp', '')}C / "
        f"vento {dados_api.get('wind', {}).get('speed', '')}m/s / "
        f"chuva {dados_api.get('rain', {}).get('3h', 0)}mm"
    )

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            prompt = (
                f"Gere uma mensagem curta, empática e preventiva para {seg['nome']}, "
                f"segurado com apólice {seg['produto']} em {cidade}. "
                f"Evento detectado: {evento_nome} ({evento_id}). Dados meteorológicos: {dados_api}. "
                f"Dê 2 dicas práticas de prevenção. Canal de envio: {seg['canal']}. Máximo 300 caracteres."
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[COMUNICADOR] LLM falhou ({e}), usando template de fallback")

    tpl = TEMPLATES.get(evento_id, "Alerta {evento_id} em {cidade} para {nome}. Tome precauções.")
    return tpl.format(nome=seg["nome"], produto=seg["produto"], cidade=cidade, detalhe=detalhe, evento_id=evento_id)


if __name__ == "__main__":
    notif = {
        "evento_id": "E01",
        "evento_nome": "CHUVA_INTENSA_RESIDENCIAL",
        "segurado": {"nome": "Ana", "produto": "Residencial", "canal": "WhatsApp"},
        "cidade": "Porto Alegre",
    }
    print(gerar_mensagem_ia(notif, {"main": {"temp": 22}, "wind": {"speed": 9}, "rain": {"3h": 54}}))
