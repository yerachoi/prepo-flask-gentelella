from datetime import datetime
import os
import re

import pandas as pd

from app.forms import blueprint
from flask import jsonify, render_template, redirect, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.base.forms import AddUrlForm
from app.base.models import Document, Url, User

import pandas as pd
from prepo.prepo.scraper import scrap
from prepo.prepo.preprocessor import preprocessing, summarize
from prepo.submodules.kakaotalk_msg_preprocessor import kakaotalk_msg_preprocessor

from prepo.submodules.Top2Vec.top2vec import Top2Vec

@blueprint.route('/<template>')
@login_required
def route_template(template, methods=('GET', 'POST')):
    print('route_template')
    # if template=='add_url': 
    #     form = AddUrlForm()
        # if request.method == 'POST' and form.validate_on_submit():
        #     url = Url(url=form.content.data, plink_date=datetime.now())
        #     db.session.add(url)
        #     db.session.commit()
        # return jsonify('success')
    # else:
    #     return render_template(template + '.html')
    # form = AddUrlForm(request.form)
    # if request.method == 'POST':
        # url = Url(url=form.content.data, plink_date=datetime.now())
        # db.session.add(url)
        # db.session.commit()
        # return redirect(url_for('forms_blueprint.index'))
        # return jsonify('success')
    return render_template(template + '.html')

def save_url(input_df, idx=None, sensitive_domain_cats=None):
    docs_info, docs_idx, error_urls_by_types = scrap(input_df['url'], idx, sensitive_domain_cats)  # .tolist()

    print(error_urls_by_types)
    
    success_url_ids = []
    failure_url_ids = []

    # scrap 성공한 경우
    if docs_info:
        docs_info_df = pd.DataFrame.from_dict(docs_info)
        if docs_idx:
            docs_info_df.index = docs_idx
            
        docs_info_df = docs_info_df.join(input_df['clip_at'], how='left')
        docs_info_df = docs_info_df.sort_values(by=['clip_at'], axis=0).reset_index(drop=True)  # 정렬 후 reset index

        # preprocess
        docs_info_prep_df = docs_info_df.copy()
        docs_info_prep_df['contents_prep'] = docs_info_prep_df['title'] + ". " + docs_info_prep_df['contents']
        docs_info_prep_df['contents_prep'] = docs_info_prep_df['contents_prep'].apply(preprocessing)
        docs_info_prep_df['contents_prep_sum'] = docs_info_prep_df['contents_prep'].apply(summarize)

        for index, row in docs_info_prep_df.iterrows():
            if pd.isnull(row['publish_date']):
                publish_date = None

            try:
                url = Url(
                    url=row['url'], 
                    clip_date=row['clip_at'],
                    crawl_date=row['crawl_at'],
                    scrap_result='success',
                    user_id=current_user.get_id(),
                    )
                db.session.add(url)
                db.session.commit()

                doc = Document(
                    title=row['title'],
                    text_raw=row['contents'],
                    text_prep=row['contents_prep'],
                    text_sum=row['contents_prep_sum'],
                    
                    clip_date=row['clip_at'],
                    crawl_date=row['crawl_at'],

                    publish_date=publish_date,                
                    is_news=row['is_news'],
                    
                    url_id=url.id
                    )            
                db.session.add(doc)
                db.session.commit()

                success_url_ids.append(url.id)

            except Exception as e: # 수정 필요: 중복 url인 경우 무시
                print(e)
                continue

    # scrap 실패한 경우
    if error_urls_by_types:
        for key in error_urls_by_types:  # 'parse_error', 'empty_contents'
            for error_url in error_urls_by_types[key]:
                try:
                    url = Url(
                        url=error_url,
                        clip_date=datetime.now(), # 수정 필요: 실패하더라도 저장한 날짜 얻을 수 있게
                        crawl_date=datetime.now(),
                        scrap_result=key,
                        user_id=current_user.get_id())
                    db.session.add(url)
                    db.session.commit()

                    failure_url_ids.append(url.id)

                except Exception as e:
                    print(e)
                    continue    

    return success_url_ids, failure_url_ids


@blueprint.route('/form', methods=['GET', 'POST'])
@login_required
def form():
    return render_template('form.html')
    

@blueprint.route('/add_url', methods=['POST'])
@login_required
def add_url():
    add_url_form = AddUrlForm(request.form)
    # if request.method == 'POST' and add_url_form.validate_on_submit():


    if request.method == 'POST':
        # print(add_url_form.data.get('content'))

        ########## input_df만들기 ################
        ### kakaotalk_export_file에서 url 추출
        # file_path = None
        # file_type = kakaotalk_msg_preprocessor.check_export_file_type(file_path)
        # messages = kakaotalk_msg_preprocessor.parse(file_type, file_path)
        # # URL만 추출. [{'datetime': datetime.datetime(2020, 8, 11, 12, 3), 'user_name': '김한길', 'url': 'https://www.youtube.com'}]
        # url_messages = kakaotalk_msg_preprocessor.url_msg_extract(file_type, messages)
        # input_df = pd.DataFrame.from_dict(url_messages)[['datetime', 'url']]
        # input_df.rename(columns = {'datetime' : 'clip_at'}, inplace = True)

        ### 또는 입력에서 URL을 request.form['url']로 가져오고 datetime.now()을 넣어서 
        # url, clip_at 칼럼을 가진 input_df을 만들어줘야함

        now = datetime.now()
        now_print = now.strftime("%Y년 %m월 %d일 %H시 %M분")

        # comma/whitespace로 구분된 url 목록인 경우
        url_list = [url.strip() for url in re.split("[;,]", request.form['url'])]
        input_df = pd.DataFrame(data={'url': url_list, 'clip_at': [datetime.now()] * len(url_list)})
        url_num = len(input_df)

        ############# 유저가 입력한 피하고 싶은 민감 url 종류. 다음의 값들을 가진 list가 들어가야 함 : "cloud", "sns/community", 'shopping', "ott", "online_meeting"
        sensitive_domain_cats=['ott', 'cloud']

        # scrap
        success_url_ids, failure_url_ids = save_url(input_df, sensitive_domain_cats=sensitive_domain_cats)
        success_doc_list = [Document.query.filter_by(url_id=url_id).one() 
                            for url_id in success_url_ids]
        failure_url_list = [Url.query.filter_by(id=url_id).one() 
                            for url_id in failure_url_ids]

        # return redirect(url_for('forms_blueprint.form'))
        return render_template(
            'form_result.html', 
            url_num=url_num,
            now_print=now_print,
            success_doc_list=success_doc_list,
            failure_url_list=failure_url_list,
            )

    else:
        return redirect(url_for('forms_blueprint.form'))


@blueprint.route('/add_url_kakao', methods=['GET', 'POST'])
@login_required
def add_url_kakao():
    print("add_url_kakao")
    if request.method == 'POST':
        now = datetime.now()
        now_print = now.strftime("%Y년 %m월 %d일 %H시 %M분")

        # load file
        try:
            f = request.files['file']
            filename = secure_filename(f.filename)
            print(filename)
            file_path = os.path.join("/mnt/d/yerachoi/plink-flask-gentelella/data/", filename)
            f.save(file_path)

            # get the device type and language of kakaotalk_export_file
            file_type = kakaotalk_msg_preprocessor.check_export_file_type(file_path)
            # parse the text from a kaotalk_export_file
            messages = kakaotalk_msg_preprocessor.parse(file_type, file_path)
            # URL만 추출
            url_messages = kakaotalk_msg_preprocessor.url_msg_extract(file_type, messages)

        except Exception as e:
            print("except case", e)
            return redirect(url_for('forms_blueprint.form'))

        # scrap
        input_df = pd.DataFrame(url_messages, columns=['url', 'datetime'])
        input_df.rename(columns = {'datetime': 'clip_at'}, inplace = True)
        url_num = len(input_df)

        ############# 유저가 입력한 피하고 싶은 민감 url 종류. 다음의 값들을 가진 list가 들어가야 함 : "cloud", "sns/community", 'shopping', "ott", "online_meeting"
        sensitive_domain_cats=['ott', 'cloud']

        # scrap
        success_url_ids, failure_url_ids = save_url(input_df, sensitive_domain_cats=sensitive_domain_cats)
        success_doc_list = [Document.query.filter_by(url_id=url_id).one() 
                            for url_id in success_url_ids]
        failure_url_list = [Url.query.filter_by(id=url_id).one() 
                            for url_id in failure_url_ids]

        # return redirect(url_for('forms_blueprint.form'))
        return render_template(
            'form_result.html', 
            url_num=url_num,
            now_print=now_print,
            success_doc_list=success_doc_list,
            failure_url_list=failure_url_list,
            )

    else:
        return redirect(url_for('forms_blueprint.form'))


# # 기존 데이터 DB 추가용 코드
# @blueprint.route('/add_url_csv', methods=['GET', 'POST'])
# @login_required
# def add_url_csv():
#     print("add_url_csv")
#     if request.method == 'POST':
#         # load file
#         try:
#             f = request.files['file']
#             filename = secure_filename(f.filename)
#             print(filename)
#             file_path = os.path.join("/mnt/d/yerachoi/plink-flask-gentelella/data/", filename)
#             f.save(file_path)

#         except Exception as e:
#             print("except case", e)
#             # return redirect(url_for('forms_blueprint.form'))

#         # load data
#         input_df = pd.read_csv(file_path)
#         print(input_df.columns)

#         for index, row in input_df.iterrows():
#             try:
#                 url = Url(
#                     url=row['url'],
#                     clip_date=pd.to_datetime(row['clip_at']),
#                     crawl_date=pd.to_datetime(row['crawl_at']),
#                     scrap_result='success',
#                     user_id=current_user.get_id(),

#                     cluster = int(row['cluster']),
#                     cluster_reduced = int(row['cluster_reduced'])
#                     )
#                 db.session.add(url)
#                 db.session.commit()

#                 if row['is_news'] == 'TRUE':
#                     is_news=True
#                 else:
#                     is_news=False

#                 print(row['title'])
#                 doc = Document(
#                     title=row['title'],
#                     text_raw=row['contents'],
#                     text_prep=row['contents_prep'],
#                     # text_sum=row['contents_prep'],
                    
#                     clip_date=pd.to_datetime(row['clip_at']),
#                     crawl_date=pd.to_datetime(row['crawl_at']),

#                     # publish_date=pd.to_datetime(row['publish_date']),                
                    
#                     is_news=is_news,
                    
#                     url_id=url.id
#                     )
#                 db.session.add(doc)
#                 db.session.commit()

#             except Exception as e:
#                 print("except case", e)
#                 print(row['title'], row['url'])

#         # return redirect(url_for('forms_blueprint.form'))
#         return render_template(
#             'form_result.html', 
#             success_doc_list=[],
#             failure_url_list=[],
#             )