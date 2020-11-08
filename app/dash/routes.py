from . import blueprint
from flask import render_template
from flask_login import login_required
# from Dashboard import Dash_App1, Dash_App2, Dash_App3, Dash_App4
from Dashboard import user_totaldoc_app, user_weekdaydoc_app 
from Dashboard import user_timeseries_app, user_clustermap_app
from Dashboard import hotkeyword_app


@blueprint.route('/app1')
@login_required
def app1_template():
    # return render_template('app1.html', dash_url = Dash_App1.url_base)
    return render_template('app1.html', dash_url = user_totaldoc_app.url_base)

@blueprint.route('/app2')
@login_required
def app2_template():
    # return render_template('app2.html', dash_url = Dash_App2.url_base)
    return render_template('app2.html', dash_url = user_weekdaydoc_app.url_base)

@blueprint.route('/app3')
@login_required
def app3_template():
    # return render_template('app3.html', dash_url = Dash_App3.url_base)
    return render_template('app3.html', dash_url = user_timeseries_app.url_base)

@blueprint.route('/app4')
@login_required
def app4_template():
    # return render_template('app4.html', dash_url = Dash_App4.url_base)
    return render_template('app4.html', dash_url = user_clustermap_app.url_base)

@blueprint.route('/app5')
@login_required
def app5_template():
    # return render_template('app5.html', dash_url = Dash_App5.url_base)
    return render_template('app5.html', dash_url = hotkeyword_app.url_base)