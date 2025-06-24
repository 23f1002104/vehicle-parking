# vehicle-parking-Vpark-1.0

---

## Models
We define our models in `./Models/models.py` as per the given descriptions in **Project Statement**. For need of furthur changes in our SQLite database we may use flask_migrate.


## Controllers
All the app routes are added here,`./Controllers/routes.py` including authentications. The authentications are handeled by `flask-login` and in future a new decorator `@admin_required` will be defined that will allow some functionalities to be Admin only.

---

## Instructions

1. Clone the repository
2. Create a virtual environment
```bash
python3 -m venv .venv
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
6. Once the database is created, create an Admin by running `create_admin.py`

---

## TODO:

---

**File Structure**
- [x] Create a file structure as per the given statement.
    - [x] Controllers
    - [x] Models
    - [x] Templates
    - [ ] Static (Unused for now, but may be used in future)
- [x] Inside `templates` create separate folders for `admin` and `user` templates.

---

**Optional**
- [ ] ~Create a folder `Api` for API related files(`api.py`,`resources.py`).~
- [x] Create a folder `Forms` for `Flask-WTF` forms (if used).
    - [ ] Use `Flask-WTF` for backend validation

---

**Frontend**
- [x] Create navbars and alert messeges (flash messeges).
- [x] Use [Modals](https://getbootstrap.com/docs/5.0/components/modal/) (BootStrap5) to book or check out parking spots. Also, may be used in Creating and deleting parking lots by admin.


---

**Backend**
- [x] Create Database as per given statement. 
    - [x] Implemented `reservation_cost` method to calculate cost
- [x] Implement authentication for users using `flask-login`
- [x] Create admins and test
- [x] Make `@admin_required` decorator to check user.is_admin
- [x] Make Admin Dashboard
- [x] Implement admin functionalities
    - [x] CRUD on parking lots
    - [x] Automatically create parking spots based on the maximum capacity of the lot.
    - [x] View parking spots details and delete a spot.
    - [x] Admin should see a list of all users and their details
    - [ ] ~Flag an user~
    - [x] Create a field in the admin dashboard to search for a user, parking lot or reservation
- [x] User dashboard (Partially created)
- [x] `@user_requied` decorator to check if user is logged in and is not an admin
- [ ] User functionalities
    - [ ] operation on parking spots
    - [ ] CRUD on `Reservation` 
    - [ ] Track timestamps for reservation and View parking history

---

**Optional**
- [x] Use flask blueprints
- [x] Search functionality for Admins
- [ ] ~API Integration~
- [ ] Try using `flask-wtf` for form validation and CSRF protection (Ongoing)
- [ ] Implement Stats page (ChartJS)
