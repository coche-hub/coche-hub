from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class CommunityForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[
            DataRequired(message='Name is required'),
            Length(min=3, max=100, message='Name must be between 3 and 100 characters')
        ]
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()]
    )
    
    logo = StringField(
        'Logo URL',
        validators=[Optional(), Length(max=255)]
    )
    
    submit = SubmitField('Create Community')
