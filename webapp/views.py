import requests
import urllib
from logging import basicConfig, getLogger, INFO as level
from flask.views import MethodView
from flask import render_template, request, jsonify, make_response, json


SHORTCODE = {
    'Холодное водоснабжение': 'ХВ',
    'Горячее водоснабжение': 'ГВ',
    'Электроэнергия (день)': 'ЭЭ (день)',
    'Электроэнергия (ночь)': 'ЭЭ (ночь)'
}

basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)

logger = getLogger('webhook')

class APIQueryError(Exception):
    pass


def create_view(app):
    app.add_url_rule("/form/", view_func=FormView.as_view("form"))
    app.add_url_rule("/dialogflow/", view_func=WebhookDialogflow.as_view("dialogflow"))
    return app


class FormView(MethodView):
    def get(self):
        return render_template("form.html", text='Hey')


def api_query(fn):
    def query(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except urllib.request.HTTPError as err:
            if err.code in (500, 503, 504):
                raise APIQueryError("Сервер недоступен")
            elif err.code == 404:
                raise APIQueryError("Неправильный лицевой счет")
            elif err.code == 408:
                raise APIQueryError("Нет ответа от сервера")
#             else:
#                 raise APIQueryError("Что-то пошло не так")
    return query


class WebhookDialogflow(MethodView):
    def post(self):
        data = request.get_json(silent=True, force=True)
        logger.info(f"Request:\n{data}")

        response = self.default()
        if data.get("queryResult").get("action") == "check.duty":
            response = self.check_duty(data)

        elif data.get("queryResult").get("action") == "check.readings":
            response = self.check_readings(data)

        elif data.get("queryResult").get("action") == "put.readings":
            response = self.put_readings(data)

        elif data.get("queryResult").get("action") == "verification":
            response = self.verification(data)

        elif data.get("queryResult").get("action") == "put.counter_reading":
            response = self.put_counter_reading(data)

        logger.info(f"Response:\n {response}")
        return make_response(jsonify(response))

    def verification(self, data):
        account = int(data.get("queryResult", dict()).get("parameters", dict()).get("account"))
        fio = data.get("queryResult", dict()).get("parameters", dict()).get("fio")
        try:
            speech = "\n".join(self.get_verify(account, fio))
        except APIQueryError as e:
            speech = str(e)

        return {'fulfillmentText': speech}
    
    def default(self):
        speech = "Произошла ошибка"
        return {'fulfillmentText': speech}

    def check_duty(self, data):
        account = int(data.get("queryResult", dict()).get("parameters", dict()).get("account"))

        try:
            speech = "\n".join(self.get_duty(account))
        except APIQueryError as e:
            speech = str(e)
        return {'fulfillmentText' : speech }
        # return {'payload': {'telegram': {"text": speech}}, "source": "tricbot"}

    def check_readings(self, data):
        account = int(data.get("queryResult", dict()).get("parameters", dict()).get("account"))
        fio = data.get("queryResult", dict()).get("parameters", dict()).get("fio")

        try:
            speech = "\n".join(self.get_readings(account, fio))
        except APIQueryError as e:
            speech = str(e)
        return {'fulfillmentText': speech}

    def put_readings(self, data):
        account = int(data.get("queryResult", dict()).get("parameters", dict()).get("account"))
        fio = data.get("queryResult", dict()).get("parameters", dict()).get("fio")

        try:
            counters = self.put_reading(account, fio)
        except APIQueryError as e:
            return {"fulfillmentText": str(e)}
        return {'fulfillmentMessages': [{'payload': {'telegram': {'text': 'Нажми на счетчик и введи показание по нему', 'reply_markup': {'inline_keyboard': [
            [{'text': self.print_counter(c), 'callback_data': f'счетчик по номеру {c["id"]}'}] for c in counters
#               по лс {account} с фамилией {fio} 
            ]}}}, 'platform': 'TELEGRAM'}], 'parameters': {'counters': "123"}}
    
    def put_counter_reading(self, data):
        counter_id = dict(data.get("queryResult", dict()).get("parameters", dict()).get("counter"))
        value = dict(data.get("queryResult", dict()).get("parameters", dict()).get("value"))

        try:
            counters = self.put_counter_readings(counter_id, value)
        except APIQueryError as e:
            return {"fulfillmentText": str(e)}
        return {'fulfillmentText': counters}

    @api_query
    def get_duty(self, account):
        r = requests.get(f'https://api.itpc.ru/v1/accounts/{account}/debt', timeout=10)
        debt = r.json()
        return (f"По вашему лицевому счету: {account}",
                f"Адрес: {debt['address']}",
                f"Ваша задолженность: {debt['amount']}")

    @api_query
    def get_readings(self, account, fio):
        with urllib.request.urlopen(
                f'https://api.itpc.ru/v1/accounts/{account}/counters?lastname={urllib.parse.quote(fio)}') as response:
            counters = json.loads(response.read())
        counters_print = []
        k=0
        for i in counters['counters']:
            k=k+1
            if counters['counters'] == ' ':
                counters_print.append(f"Счетчики отсутствуют!")
            if i['place'] is None or i['model'] is None:
                counters_print.append(f"{k}. Место не указано: {SHORTCODE.get(i['name'])}. {i['currReadings']}")
            else:
                counters_print.append(f"{k}. {i['place']}: {i['model']}. {SHORTCODE.get(i['name'])}. {i['currReadings']}")
        return (f"Адрес: {counters['address']}:"," ") + tuple(counters_print)

    @api_query
    def get_verify(self, account, fio):
        with urllib.request.urlopen(
                f'https://api.itpc.ru/v1/accounts/{account}/counters?lastname={urllib.parse.quote(fio)}') as response:
            counters = json.loads(response.read())
        counters_print = []
        k=0
        for i in counters['counters']:
            k=k+1
            if counters['counters'] == ' ':
                counters_print.append(f"Счетчики отсутствуют!")
            if  i['nextVerificationRemaining'] < 0 or i.get('place') is None:
                counters_print.append(f"{k}. {i['model']} {SHORTCODE.get(i['name'])}. {i['nextVerificationMessage']}!")
            else:
                counters_print.append(f"{k}. ({SHORTCODE.get(i['name'])})"
                                      f"({i['place']}). До следующей поверки {i['nextVerificationRemaining']} дн.")
        return (f"Адрес: {counters['address']}", "Счетчики:") + tuple(counters_print)
   
    @api_query
    def put_reading(self, account, fio):
        with urllib.request.urlopen(
                f'https://api.itpc.ru/v1/accounts/{account}/counters?lastname={urllib.parse.quote(fio)}') as response:
            counters = json.loads(response.read())
        return counters['counters']

    def print_counter(self, counter):
        if counter['place'] is None or counter['model'] is None:
            return f"{SHORTCODE.get(counter['name'])}. {counter['currReadings']}"
        return f"{counter['place']}: {counter['model']}. {SHORTCODE.get(counter['name'])}. {counter['currReadings']}"

    def put_counter_readings(self, counter_id, value):
        return f"{counter_id}, {value}"