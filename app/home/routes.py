from datetime import datetime, timedelta
from sqlalchemy import func

from app.home import blueprint
from flask import render_template
from flask_login import login_required

# from Dashboard import Dash_App1, Dash_App2, Dash_App3, Dash_App4
from Dashboard import user_totaldoc_app, user_weekdaydoc_app 
from Dashboard import user_timeseries_app, user_clustermap_app

from app.base.models import Document


@blueprint.route('/index')
@login_required
def index():
    doc_list = Document.query.order_by(Document.crawl_date.desc())
    doc_num = Document.query.count()
    
    datetime_lastweek = datetime.today() - timedelta(days=6)
    datetime_lastweek = datetime_lastweek.replace(hour=0, minute=0, second=0, microsecond=0)
    doc_num_lastweek = Document.query.filter(Document.crawl_date >= datetime_lastweek).count()
    
    return render_template(
        'index2.html', 
        doc_list=doc_list, doc_num=doc_num,
        doc_num_lastweek=doc_num_lastweek,
        # dash_url=user_totaldoc_app.url_base
        )


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')