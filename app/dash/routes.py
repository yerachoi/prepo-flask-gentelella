from . import blueprint
from flask import render_template
from flask_login import login_required
from Dashboard import Dash_App1, Dash_App2

@blueprint.route('/app1')
@login_required
def app1_template():
    return render_template('app1.html', dash_url = user_timeseries_app.url_base)

@blueprint.route('/app2')
@login_required
def app2_template():
    return render_template('app2.html', dash_url = user_totaldoc_app.url_base)

@blueprint.route('/app3')
@login_required
def app2_template():
    return render_template('app3.html', dash_url = user_weekdaydoc_app.url_base)

@blueprint.route('/app4')
@login_required
def app2_template():
    return render_template('app4.html', dash_url = user_clustermap_app.url_base)