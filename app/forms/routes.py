from datetime import datetime

from app.forms import blueprint
from flask import jsonify, render_template, redirect, request, url_for
from flask_login import current_user, login_required

from app import db
from app.base.forms import AddUrlForm
from app.base.models import Document, Url, User

from plink.src.scrap import scraper
from plink.src.preprocess import preprocessing, summarizer

# @blueprint.route('/<template>')
# @login_required
# def route_template(template, methods=('GET', 'POST')):
#     print('route_template')
#     # if template=='add_url': 
#     #     form = AddUrlForm()
#         # if request.method == 'POST' and form.validate_on_submit():
#         #     url = Url(url=form.content.data, plink_date=datetime.now())
#         #     db.session.add(url)
#         #     db.session.commit()
#         # return jsonify('success')
#     # else:
#     #     return render_template(template + '.html')
#     # form = AddUrlForm(request.form)
#     # if request.method == 'POST':
#         # url = Url(url=form.content.data, plink_date=datetime.now())
#         # db.session.add(url)
#         # db.session.commit()
#         # return redirect(url_for('forms_blueprint.index'))
#         # return jsonify('success')
#     return render_template(template + '.html')


@blueprint.route('/form', methods=['GET', 'POST'])
@login_required
def form():
    return render_template('form.html')
    

@blueprint.route('/add_url', methods=['POST'])
@login_required
def add_url():
    print(request.form['url'])
    add_url_form = AddUrlForm(request.form)
    # if request.method == 'POST' and add_url_form.validate_on_submit():
    if request.method == 'POST':
        # print(add_url_form.data.get('content'))
        url = Url(url=request.form['url'], 
                  plink_date=datetime.now(),
                  user_id=current_user.get_id())
        db.session.add(url)
        db.session.commit()

        docs_info, docs_idx, error_urls_by_types = scraper([request.form['url']])
        text_raw = docs_info[0]['contents']
        if text_raw:
            try:
                text_sum = summarizer(text_raw)
                text_prep = preprocessing(text_sum)
            except:
                text_prep = preprocessing(text_raw)

            doc = Document(
                title=docs_info[0]['title'],
                publish_date=docs_info[0]['publish_date'],
                text_raw=text_raw,
                text_prep=text_prep,
                text_sum=text_sum,
                crawl_date=docs_info[0]['crawl_at'],
                is_news=docs_info[0]['is_news'],
            )
            db.session.add(doc)
            db.session.commit()

            print(preprocessing(docs_info[0]['contents']))
            
        else:
            print(error_urls_by_types)

        return redirect(url_for('forms_blueprint.form'))
    else:
        return redirect(url_for('forms_blueprint.form'))

# @blueprint.route('/<template>/add_url', methods=('GET', 'POST'))
# @login_required
# def add_url():
#     # form = AddUrlForm(request.form)
#     # if request.method == 'POST' and form.validate_on_submit():
#     print('add_url')
#     print(request)
#     if request.method == 'POST':
#         # url = Url(url=form.content.data, plink_date=datetime.now())
#         # db.session.add(url)
#         # db.session.commit()
#         # return redirect(url_for('forms_blueprint.index'))
#         return jsonify('success')
#     else:
#         return render_template('errors/page_403.html')