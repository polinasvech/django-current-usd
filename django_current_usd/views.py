from django.http import HttpResponse
import datetime as dt
import json
from django.conf import settings
import requests
from collections import namedtuple


def get_latest_usd_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "RUB"
) -> (int, float):
    """
    Посылает запрос к api и получает текущее значение курса

    :param currency_from: валюта, которую нужно перевести
    :param currency_to: валюта, в которую нужно перевести

    :return ts: timestamp запроса
    :return exchange_rate: текущее значение курса
    """
    api_key = settings.API_KEY

    usd_info = requests.get(
        f"https://api.apilayer.com/exchangerates_data/latest?symbols={currency_to}&base={currency_from}",
        headers={"apikey": api_key},
    )
    usd_info = json.loads(usd_info.content.decode('utf-8'))

    return usd_info["timestamp"], usd_info["rates"][currency_to]


def current_usd(request):
    ExchangeRateInfo = namedtuple('ExchangeRateInfo', ["timestamp", "rate"])
    rates_history_file = "django_current_usd/ext_rates.json"

    try:
        with open(rates_history_file, 'r') as f:
            data = json.load(f)
    except json.decoder.JSONDecodeError:
        data = {
            "history": []
        }

    if len(data["history"]):
        # т.к. нужно показать историю последних 10 запросов, удаляем из списка
        # самый ранний запрос
        if len(data["history"]) > 10:
            del data["history"][0]

        if dt.datetime.timestamp(dt.datetime.now()) - data["history"][-1]["timestamp"] > 100:
            # Если с момента последнего обновления прошло более 10 секунд, обновляем данные
            ts, exchange_rate = get_latest_usd_exchange_rate()
            ext_rate_info = ExchangeRateInfo(ts, exchange_rate)
            data["history"].append(ext_rate_info._asdict())
        else:
            exchange_rate = data["history"][-1]["rate"]
    else:
        ts, exchange_rate = get_latest_usd_exchange_rate()
        ext_rate_info = ExchangeRateInfo(ts, exchange_rate)
        data["history"] = [ext_rate_info._asdict()]

    with open(rates_history_file, 'w') as f:
        json.dump(data, f)

    info = f"Current dollar to ruble exchange rate: 1 USD = {'{:.2f}'.format(exchange_rate)} RUB"
    body = f"<h2>{info}</h2>"

    if len(data["history"]) - 1:
        body += "<div>Request history</div> <ul>"
        for info in data["history"][-2::-1]:
            body += (
                f"<li> 1 USD = {'{:.4f}'.format(info['rate'])} RUB "
                f"({dt.datetime.fromtimestamp(info['timestamp']).strftime('%d.%m.%Y %H:%M:%S')})</li>"
            )
        body += "</ul>"
    else:
        body += "<div>Request history is empty</div>"

    return HttpResponse(f"<html><body>{body}</body></html>")
