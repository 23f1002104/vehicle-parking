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


@main_bp.route("/search")
def search():
    from rapidfuzz import fuzz, utils
    from flask import request
    from Models.models import ParkingLot
    query = request.args.get("query", "").strip()

    if not query:
        return render_template("main/search.html", results=[lot for lot in ParkingLot.query.all()], query=query)

    processed_query = utils.default_process(query)
    threshold = 80 # needs to be adjusted for better results
    results = []
    for lot in ParkingLot.query.all():
        for col in lot.__table__.columns:
            score = fuzz.token_set_ratio(
                processed_query,
                str(getattr(lot, col.name)),
                processor=utils.default_process
            )
            print(score, col.name)
            if score > threshold:
                results.append(lot)
                break

    # Deduplicate the results based on the id 
    results_list = list({getattr(obj, 'id'): obj for obj in results}.values())
    # final result
    results = results_list if len(results_list) > 0 else ["Try using better query or field. Could not find better match"]
    # print(results, type(query)) # Debugging

    return render_template("main/search.html", results=results, query=query)