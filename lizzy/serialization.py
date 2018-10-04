import connexion.apps.flask_app as flask_app

from .models.stack import Stack


class JSONEncoder(flask_app.FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Stack):
            stack_dict = {"creation_time": o.creation_time,
                          "description": o.description,
                          "stack_name": o.stack_name,
                          "status": o.status,
                          "version": o.version}
            return stack_dict

        return super().default(o)
