# vehicle-parking

---

## Models
We define our models in `./Models/models.py` as per the given descriptions in **Project Statement**. For need of furthur changes in our SQLite database we may use flask_migrate.


## Controllers
All the app routes are added here,`./Controllers/routes.py` including authentications. The authentications are handeled by `flask-login` and in future a new decorator `@admin_required` will be defined that will allow some functionalities to be Admin only.
---

## TODO:

- [x] Create Database as per given statement. 
- [x] Implement authentication for users using `flask-login`
- [ ] Create admins and test
- [ ] Make `@admin_required` decorator to check user.is_admin
- [ ] Make Admin Dashboard
- [ ] Implement admin functionalities
    - [ ] CRUD on parking lots
    - [ ] Automatically create parking spots based on the maximum capacity of the lot.
    - [ ] View parking spots details.
    - [ ] Admin should see a list of all users and their details
    - [ ] ~Flag an user~
    - [ ] Create a field in the admin dashboard to search for a user or spot to see if a spot is vacant or occupied 
- [ ] User dashboard
- [ ] User functionalities
    - [ ] CRUD on parking spots
    - [ ] Track timestamps for reservation and View parking history



**Optional**
- [ ] API Integration
- [ ] Implement Stats page (ChartJS)
- [ ] Use flask blueprints
- [ ] ~Try using `flask-wtf` for form validation and CSRF protection~