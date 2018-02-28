from flask_script import Manager
import os

from webapp.assets import create_app

app = create_app()
manager = Manager(app)

@manager.command
def runserver():
    """ Runserver with socketio support """
    return app.run(
        host='127.0.0.1',
        port=int(os.environ.get('PORT', 7777)),
        use_debugger=False,
        use_reloader=False
    )

if __name__ == '__main__':
    manager.run()