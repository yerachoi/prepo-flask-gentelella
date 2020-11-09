from app.tables import blueprint
from app.base.models import Document, Url, User
from flask import render_template
from flask_login import login_required


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')

@blueprint.route('/<int:doc_id>/')
def doc_detail(doc_id):
    doc = Document.query.get(doc_id)
    return render_template('document_table.html', doc=doc)