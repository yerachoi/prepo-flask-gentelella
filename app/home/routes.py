from sqlalchemy import func

from app.home import blueprint
from flask import render_template
from flask_login import login_required

from Dashboard import Dash_App1, Dash_App2

from app.base.models import Document


@blueprint.route('/index')
@login_required
def index():
    doc_list = Document.query.order_by(Document.crawl_date.desc())
    doc_num = Document.query.count()
    return render_template(
        'index2.html', 
        doc_list=doc_list, doc_num=doc_num,
        dash_url=Dash_App1.url_base
        )


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')