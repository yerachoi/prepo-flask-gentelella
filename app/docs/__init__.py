from flask import Blueprint

blueprint = Blueprint(
    'docs_blueprint',
    __name__,
    url_prefix='/docs',
    template_folder='templates',
    static_folder='static'
)
