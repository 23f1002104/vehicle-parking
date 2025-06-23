from flask import render_template
from . import main_bp


#? main.py
@main_bp.route("/")
def index():
    return render_template("main/index.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/features")
def features():
    return render_template("main/features.html")


@main_bp.route("/services")
def services():
    return render_template("main/services.html")

@main_bp.route("/stats")
def stats():
    return render_template("main/stats.html")