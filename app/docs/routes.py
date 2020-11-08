from app.docs import blueprint
from app.base.models import Document, Url, User
from flask import render_template
from flask_login import login_required


@blueprint.route('/<template>')
@login_required
def route_template(template):
    doc_list = Document.query.order_by(Document.clip_date.desc())
    return render_template(template + '.html', doc_list=doc_list)


@blueprint.route('/<int:doc_id>/')
def doc_detail(doc_id):
    doc = Document.query.get(doc_id)
    return render_template('docs_table.html', doc=doc)