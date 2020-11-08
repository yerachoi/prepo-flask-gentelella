from datetime import datetime, timedelta

from app.docs import blueprint
from app.base.models import Document, Url, User
from flask import render_template
from flask_login import current_user, login_required

from prepo.submodules.Top2Vec.top2vec import Top2Vec

@blueprint.route('/<template>')
@login_required
def route_template(template):
    user_id=current_user.get_id()
    doc_list = Document.query.join(Url).filter(Url.user_id==user_id).order_by(Document.clip_date.desc())
    
    datetime_lastweek = datetime.today() - timedelta(days=6)
    datetime_lastweek = datetime_lastweek.replace(hour=0, minute=0, second=0, microsecond=0)
    doc_lastweek_list = Document.query.join(Url).filter(Url.user_id == user_id, 
                                                        Url.scrap_result=='success', 
                                                        Url.crawl_date >= datetime_lastweek)

    return render_template(template + '.html', 
                           doc_list=doc_list,
                           doc_lastweek_list=doc_lastweek_list)


@blueprint.route('/<int:doc_id>/')
@login_required
def doc_detail(doc_id):
    user_id=current_user.get_id()
    doc = Document.query.get(doc_id)

    tm_model_path = "/mnt/d/yerachoi/plink-flask-gentelella/data/tm_test.model"
    tm_model = Top2Vec.load(tm_model_path)

    # topic
    try:
        topic_id = doc.url.cluster
        topic_info = tm_model.get_topics_info()[topic_id]['topic_words']
    except Exception as e:
        print(e)
        topic_info = []

    # topic_reduced
    try:
        topic_reduced_id = doc.url.cluster_reduced
        topic_reduced_info = tm_model.get_topics_info()[topic_reduced_id]['topic_words']
    except Exception as e:
        print(e)
        topic_reduced_info = []

    return render_template('docs_detail.html', 
                           doc=doc,
                           topic_info=topic_info,
                           topic_reduced_info=topic_reduced_info)