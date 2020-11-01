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

        # 다음 부분에 카톡대화파일에서 URL/시간 추출하거나
        # 또는 입력에서 URL을 request.form['url']로 가져오고 datetime.now()을 넣어서 
        # url, clip_at 칼럼을 가진 input_df을 만들어줘야함
        # input_df = 

        # scrap
        docs_info, docs_idx, error_urls_by_types = scraper(input_df['url'], input_df.index)  # .tolist()
        docs_info_df = pd.DataFrame.from_dict(docs_info)
        docs_info_df.index = docs_idx

        docs_info_df = docs_info_df.join(input_df['clip_at'], how='left')
        docs_info_df = docs_info_df.sort_values(by=['clip_at'], axis=0).reset_index(drop=True)  # 정렬 후 reset index

        # preprocess
        docs_info_prep_df = docs_info_df.copy()
        docs_info_prep_df['contents_prep'] = docs_info_prep_df['title'] + ". " + docs_info_prep_df['contents']
        docs_info_prep_df['contents_prep'] = docs_info_prep_df['contents_prep'].apply(preprocessing)
        docs_info_prep_df['contents_prep_sum'] = docs_info_prep_df['contents_prep'].apply(summarizer)

        for index, row in docs_info_prep_df.iterrows():
            doc = Document(
                title=row['title'],
                text_raw=row['contents'],
                text_prep=row['contents_prep'],
                text_sum=row['contents_prep_sum'],
                
                clip_date=row['clip_at'],
                crawl_date=row['crawl_at'],

                publish_date=row['publish_date'],                
                is_news=row['is_news'],
            )
            db.session.add(doc)
            db.session.commit()

            url = Url(url=row['url'], 
                plink_date=row['clip_at'],
                saved_date=row['crawl_at'],
                scrap_result='success',
                user_id=current_user.get_id())
            db.session.add(url)
            db.session.commit()

        for key in error_urls_by_types:  # 'parse_error', 'empty_contents'
            for url in error_urls_by_types[key]:
                Url(url=url, 
                    plink_date=datetime.now(),  # 추후 수정 필요
                    saved_date=datetime.now(),
                    scrap_result=key,
                    user_id=current_user.get_id())
                db.session.add(url)
                db.session.commit()

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