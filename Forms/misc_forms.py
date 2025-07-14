from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp


class ReservationForm(FlaskForm):
    car_id = StringField(
        'Car ID', 
        validators=[
            DataRequired(message="Car ID is required."),
            Regexp(
                r'^[A-Z]{2}-\d{2}-[A-Z]{1,2}-\d{4}$',
                message="Car number must be in the format XX-00-X[X]-0000."
            )
        ]
    )
    username = StringField('Username', validators=[DataRequired(message="Username is required.")])
    lot_id = StringField('Lot ID', validators=[DataRequired(message="Lot ID is required.")])
    prime_loc_name = StringField('Prime Location Name', validators=[DataRequired(message="Prime Location Name is required.")])
    spot_id = StringField('Spot ID', validators=[DataRequired(message="Spot ID is required.")])
    submit = SubmitField('Reserve Spot')
        