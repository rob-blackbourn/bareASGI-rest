"""Helper functions"""


from bareasgi import Application
import bareasgi_jinja2
import jinja2
import pkg_resources


def add_swagger_ui(app: Application) -> None:
    """Add the Swagger UI

    Args:
        app (Application): The bareASGI application
    """
    templates = pkg_resources.resource_filename("bareasgi_rest", "templates")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        enable_async=True
    )
    bareasgi_jinja2.add_jinja2(app, env)
