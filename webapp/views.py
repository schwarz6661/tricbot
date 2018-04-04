from flask.views import MethodView
from flask import render_template, request, jsonify, make_response

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
        
        return make_response()

    def get_duty(self, account):
        return 1000.05

    def check_duty(self, data):
        account = data.get("result", dict()).get("parameters", dict()).get("account")
        speech = "Долг по счету {} равен {}".format(account, self.get_duty(account))

        return {"speech": speech, "displayText": speech, "source": "tricbot"}
