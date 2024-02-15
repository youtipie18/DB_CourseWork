from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, MultipleFileField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileAllowed
from flask_ckeditor import CKEditorField

from models import Category


class LoginUser(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterUser(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class AddProduct(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Enter name for PC!")])
    price = FloatField("Price", validators=[DataRequired("You must enter the valid price!")])
    description = CKEditorField("Product Description", validators=[DataRequired("Enter the description of PC!")])
    images = MultipleFileField(validators=[FileAllowed(["jpg", "png", "webp"], "Images only!")])
    submit = SubmitField("Add Product")


class AddPart(FlaskForm):
    name = StringField("Part name", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired("You must enter the valid price!")])
    category = QuerySelectField(query_factory=lambda: Category.query, allow_blank=False, get_label="name")
    images = MultipleFileField(validators=[FileAllowed(["jpg", "png"], "Images only!")])
    submit = SubmitField("Add part")


class Checkout(FlaskForm):
    phone_number = StringField("Phone number", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    countries = []

    with open('instance/countries.txt', 'r') as file:
        for line in file:
            country_data = line.strip().split(', ')
            countries.append((country_data[0], country_data[1]))

    country = SelectField('Country', choices=countries, validators=[DataRequired()])
    submit = SubmitField("Pay")
