# vehicle-parking-Vpark-1.0

---

## Models
We define our models in `./Models/models.py` as per the given descriptions in **Project Statement**. For need of furthur changes in our SQLite database we **may** use `flask_migrate`.


## Controllers
All the app routes are added here,`./Controllers/routes.py` including authentications. The authentications are handeled by `flask-login`. A new decorator `@admin_required` is defined that will allow some functionalities to be Admin only. Similarly `@user_required` is defined to allow some funtionalities to be user only, admins are not allowed.

---

## Instructions

1. Clone the repository
```bash
gh repo clone AbhrojyotiGhosh/vehicle-parking
```
2. Create a virtual environment and activate
```bash
python3 -m venv .venv
cd .venv/bin/activte
```
3. Install `requirements.txt` by
```bash
pip install -r requirements.txt
```
4. Create `.env` file to configure application
5. Run the app by using
```bash
flask run
```
6. Once the database is created, to create an Admin manually by running `create_admin.py`(if needed, else it will be created automatically when the app is run for the first time)

---

## Overview
The entire app is built within flask framework and html5 frontend. The Users are able to see summary make reservations. The parking cost will be automatically calculated. Admins are allowed to create parking lots along with spots. Negetive number of spots or 0 spot in a lot is not allowed. Admins can also delete a spot if not currently in use. Same goes for the deletion of a parking lot.

## Future additions
* Using Flask-OAuth, Flask-Security
* Make better and more responsive UI with javascript
* Use API resources to connect backend and frontend