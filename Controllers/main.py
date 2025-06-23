from ast import main
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
        return render_template("admin/admin_search.html", results=["No query passed. Try passing some query"], query=query)
    
    processed_query = utils.default_process(query)
    threshold = 80 # needs to be adjusted for better results
    results = []

    # ParkingLot Search
    
    for lot in ParkingLot.query.all():
        combined = " ".join(filter(None, [lot.prime_location_name, lot.address, lot.pin_code]))
        score = fuzz.WRatio(processed_query, combined, processor=utils.default_process, score_cutoff=threshold)
        # print(score)
        if score > threshold:
            results.append(lot)
        else:
            pass # print(f"Try using better query. Could not find better match")

    # Deduplicate by object ID
    results_list = list({getattr(obj, 'id', id(obj)): obj for obj in results}.values())
    results = results_list if len(results_list) > 0 else ["Try using better query or field. Could not find better match"]
    # print(results, type(query)) # Debugging

    return render_template("main/search.html", results=results, query=query)