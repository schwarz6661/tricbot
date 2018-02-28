from flask_script import Manager

from webapp.assets import create_app

app = create_app()
manager = Manager(app)

@manager.command
def runserver():
    """ Runserver with socketio support """
    return app.run(
        host='0.0.0.0',
        port=443,
        use_debugger=False,
        use_reloader=False
    )

if __name__ == '__main__':
    manager.run()