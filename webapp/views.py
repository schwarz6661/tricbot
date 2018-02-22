from flask.views import MethodView
from flask import render_template

def create_view(app):
    app.add_url_rule("/form/", view_func=FormView.as_view("form"))
    return app

class FormView(MethodView):
    def get(self):
        return render_template("form.html", text="Hey!")


    