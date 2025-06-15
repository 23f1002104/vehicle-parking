## vehicle-parking

# ✅ Project TODO: Flask App

- [ ] Implement authentication for users using `flask-login`
- [ ] ~Try using `flask-wtf` for form validation and CSRF protection~

---

# Models
We define our models in `models/models.py` as per the given descriptions in **Project Statement**. For need of furthur changes in our SQLite database we use flask_migrate.

---


# Avoiding Circular Imports with `current_app`

In this project, the main Flask `app` instance is defined in `app.py`. Since our route definitions and other logic reside in separate modules, importing `app` directly from `app.py` leads to **circular import issues**.

To handle this cleanly, we use:

```python
from flask import current_app as app