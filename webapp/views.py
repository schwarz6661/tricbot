import urllib
from flask.views import MethodView
from flask import render_template, request, jsonify, make_response, json


class APIQueryError(Exception):
    pass


def create_view(app):
    app.add_url_rule("/form/", view_func=FormView.as_view("form"))
    app.add_url_rule("/dialogflow/", view_func=WebhookDialogflow.as_view("dialogflow"))
    return app


class FormView(MethodView):
    def get(self):
        return render_template("form.html", text='Hey')


class WebhookDialogflow(MethodView):
    def post(self):
        data = request.get_json(silent=True, force=True)

        if data.get("result").get("action") == "check.duty":
            return make_response(jsonify(self.check_duty(data)))

        if data.get("result").get("action") == "check.readings":
            return make_response(jsonify(self.check_readings(data)))

        return make_response()

    def get_duty(self, account):
        try:
            if account.isdigit():
                with urllib.request.urlopen(f'https://api.itpc.ru/v1/accounts/{account}/debt') as response:
                    debt = json.loads(response.read())

                return (f"По вашему лицевому счету: {account}",
                        f"Адрес: {debt['address']}",
                        f"Ваша задолженность: {debt['amount']}")
            else:
                raise APIQueryError('Введите число!')
        except urllib.request.HTTPError as err:
            if err.code == 500:
                raise APIQueryError("Сервер недоступен")
            elif err.code == 404:
                raise APIQueryError("Неправильный лицевой счет")
            else:
                raise APIQueryError("Что-то пошло не так")

    

    def get_readings(self, account, fio):
        try:
            if account.isdigit():
                with urllib.request.urlopen(
                        f'https://api.itpc.ru/v1/accounts/{account}/counters?lastname={fio}') as response:
                    debt = json.loads(response.read())

                return (f"Адрес: {debt['address']}",
                        f"Местоположение: {debt['place']}",
                        f"Название: {debt['name']}",
                        f"Модель: {debt['model']}")
            else:
                raise APIQueryError('Введите число!')
        except urllib.request.HTTPError as err:
            if err.code == 500:
                raise APIQueryError("Сервер недоступен")
            elif err.code == 404:
                raise APIQueryError("Неправильный лицевой счет")
            else:
                raise APIQueryError("Что-то пошло не так")



    def check_duty(self, data):
        account = data.get("result", dict()).get("parameters", dict()).get("account")
        try:
            speech = "\n".join(self.get_duty(account))
        except APIQueryError as e:
            speech = str(e)

        return {"speech": speech, "displayText": speech, "source": "tricbot"}


    def check_readings(self,data):
        account = data.get("result", dict()).get("parameters", dict()).get("account")
        fio = data.get("result", dict().get("parameters", dict()).get("fio"))
        try:
            speech = "\n".join(self.get_readings(account, fio))
        except APIQueryError as e:
            speech = str(e)
        return {"speech": speech, "displayText": speech, "source": "tricbot"}