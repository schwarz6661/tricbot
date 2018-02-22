from flask_script import Manager

from webapp.assets import create_app

app = create_app()
manager = Manager(app)

@manager.command
def runserver():
    """ Runserver with socketio support """
    return app.run(
        host='127.0.0.1',
        port=7777,
        use_debugger=True,
        use_reloader=True
    )

if __name__ == '__main__':
    manager.run()