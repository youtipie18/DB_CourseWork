import os
import random

from flask import Flask, render_template, redirect, url_for, flash, abort, request, jsonify, send_file
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
import functools
import datetime
import xlsxwriter
import io

from db import db_init, db
from forms import LoginUser, RegisterUser, AddPart, AddProduct, Checkout
from models import User, Product, Part, Category, ProductImage, PartImage, CharacteristicName, Characteristic, Order, \
    ProductCart, ProductOrder
from mail_controller import MailController

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_init(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(func):
    @functools.wraps(func)
    def wrap_func(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.is_admin:
                return func(*args, **kwargs)
        abort(403, "Admin Only")

    return wrap_func


def protected(func):
    @functools.wraps(func)
    def wrap_func(*args, **kwargs):
        if current_user.is_authenticated:
            return func(*args, **kwargs)
        flash('You have to log in to make your custom PC!')
        return redirect('login')

    return wrap_func


@app.route("/")
def home():
    products = Product.query.filter_by(made_by_user=False).all()
    return render_template("index.html", products=products)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginUser()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterUser()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        if User.query.filter_by(email=email).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        new_user = User()
        new_user.email = email
        new_user.password = generate_password_hash(password, salt_length=16)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route("/product<int:id>", methods=["POST", "GET"])
def product_page(id):
    product = Product.query.filter_by(id=id).first()
    if request.method == "POST":
        if current_user.is_authenticated:
            association = ProductCart(quantity=request.form['quantity'])
            association.product = product
            current_user.cart.append(association)
            db.session.commit()
            return redirect(url_for("product_page", id=id))
    return render_template("product_page.html", product=product)


@app.route("/checkout", methods=["POST", "GET"])
@login_required
def checkout():
    form = Checkout()
    if form.validate_on_submit():
        if len(current_user.cart):
            shipping_price = 0 if form.country.data == "United States" else 50
            # payment_method = request.form["pay_option"]
            phone_number = form.phone_number.data
            address = form.address.data
            order = Order(
                user=current_user,
                total_price=sum(item.product.price * item.quantity for item in current_user.cart),
                phone_number=phone_number,
                address=f"{form.country.data}, {address}",
                date=datetime.datetime.now(),
                shipping_price=shipping_price,
                # payment_method=payment_method
            )

            for product_association in current_user.cart:
                association = ProductOrder(quantity=product_association.quantity)
                association.product = product_association.product
                order.products.append(association)

            db.session.add(order)
            ProductCart.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            return render_template("success.html")
        else:
            flash("You don't have any products in your cart!")
    return render_template("checkout.html", form=form)


@app.route("/add-user-product", methods=["GET", "POST"])
@protected
def add_user_product():
    categories = Category.query.all()
    if request.method == "POST":
        new_product = Product(
            name="Your PC",
            price=request.form.get("price"),
            made_by_user=True
        )

        for part in request.form.get("selected_parts").split(";"):
            new_product.parts.append(Part.query.get(int(part.split("_")[-1])))

        image = ProductImage(
            name="user-made-pc.jpg",
            product=new_product
        )
        db.session.add(image)
        db.session.add(new_product)

        association = ProductCart(quantity=request.form['quantity'])
        association.product = new_product
        current_user.cart.append(association)

        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_user_product.html", categories=categories)


@app.route("/add-product", methods=["GET", "POST"])
@admin_only
def add_product():
    categories = Category.query.all()
    form = AddProduct()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
        )

        for part in request.form.get("selected_parts").split(";"):
            new_product.parts.append(Part.query.get(int(part.split("_")[-1])))

        for file in form.images.data:
            file_filename = secure_filename(file.filename)
            save_place = "static/product_images"
            while os.path.exists(os.path.join(save_place, file_filename)):
                name = file_filename.split(".")[0]
                mimetype = file_filename.split(".")[1]
                file_filename = "".join(name + "_copy." + mimetype)
            file.save(os.path.join(save_place, file_filename))
            image = ProductImage(
                name=file_filename,
                product=new_product
            )
            db.session.add(image)

        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_product.html", form=form, categories=categories)


@app.route("/update<int:id>", methods=["POST", "GET"])
def update(id):
    categories = Category.query.all()
    product = Product.query.get(id)
    form = AddProduct(obj=product)
    parts = ";".join(f"{part.category.name}_{part.id}" for part in product.parts).replace(" ", "")

    if form.validate_on_submit():
        product.parts = []
        if "".join([secure_filename(file.filename) for file in form.images.data]):
            for image in product.images:
                try:
                    os.remove(os.path.join("static/product_images", image.name))
                except FileNotFoundError:
                    pass
                db.session.delete(image)

            product.images = []

            for file in form.images.data:
                file_filename = secure_filename(file.filename)
                save_place = "static/product_images"
                while os.path.exists(os.path.join(save_place, file_filename)):
                    name = file_filename.split(".")[0]
                    mimetype = file_filename.split(".")[1]
                    file_filename = "".join(name + "_copy." + mimetype)
                file.save(os.path.join(save_place, file_filename))
                image = ProductImage(
                    name=file_filename,
                    product=product
                )
                db.session.add(image)
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data

        for part in request.form.get("selected_parts").split(";"):
            product.parts.append(Part.query.get(int(part.split("_")[-1])))

        db.session.commit()
        return redirect(url_for("home"))
    return render_template("update_product.html", product_id=id, form=form, categories=categories,
                           images=["static/product_images/" + image.name for image in product.images],
                           parts=parts)


# def process_c_value(name, value):
#     def is_num(x):
#         try:
#             return float(x) is not None
#         except:
#             return False
#
#     splits = value.split(" ")
#     if name == "RAM memory capacity":
#         for split in splits:
#             if is_num(split.strip()):
#                 split = int(split)
#                 return split if split >= 1000 else split * 1000
#
#     elif name == "Warranty":
#         for split in splits:
#             if is_num(split.strip()):
#                 split = float(split)
#                 return split if split >= 12 else split * 12
#
#     else:
#         return value


@app.route("/add-part", methods=["GET", "POST"])
@admin_only
def add_part():
    form = AddPart()
    if form.validate_on_submit():
        new_part = Part(
            name=form.name.data,
            price=form.price.data,
            category=form.category.data,
        )

        c_name = request.form.getlist('c_name[]')
        c_value = request.form.getlist('c_value[]')
        # sortable_names = ("RAM memory capacity", "Warranty")
        for characteristic in zip(c_name, c_value):
            new_characteristic = Characteristic(
                characteristic_id=CharacteristicName.query.filter_by(name=characteristic[0]).first().id,
                # display_value=characteristic[1],
                # value=process_c_value(characteristic[0], characteristic[1]) if characteristic[0] in sortable_names else
                # characteristic[1],
                # sortable=1 if characteristic[0] in sortable_names else 0
                value=characteristic[1]
            )
            new_part.characteristics.append(new_characteristic)

        for file in form.images.data:
            file_filename = secure_filename(file.filename)
            save_place = "static/part_images"
            while os.path.exists(os.path.join(save_place, file_filename)):
                name = file_filename.split(".")[0]
                mimetype = file_filename.split(".")[1]
                file_filename = "".join(name + "_copy." + mimetype)
            file.save(os.path.join(save_place, file_filename))
            image = PartImage(
                name=file_filename,
                part=new_part
            )
            db.session.add(image)

        db.session.add(new_part)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_part.html", form=form,
                           data=[""] + [item.name for item in CharacteristicName.query.all()])


@app.route('/delete<int:id>')
@admin_only
def delete(id):
    product = Product.query.filter_by(id=id).first()

    if product.id in [order.product_id for order in ProductOrder.query.all()]:
        abort(400, "You can't delete this product, some users have it in theirs orders.")
    else:
        for image in product.images:
            try:
                os.remove(os.path.join("static/product_images", image.name))
            except FileNotFoundError:
                pass
            db.session.delete(image)
        ProductCart.query.filter_by(product_id=product.id).delete()
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("home"))


@app.route('/delete_product', methods=['POST'])
@login_required
def delete_product():
    product_id = request.form.get('productId')

    ProductCart.query.filter_by(product_id=product_id, user_id=current_user.id).delete()
    db.session.commit()

    return jsonify({'success': True, 'total': sum([item.product.price * item.quantity for item in current_user.cart])})


@app.route('/orders')
@admin_only
def orders():
    str_start_date = request.args.get('start_date')
    str_end_date = request.args.get('end_date')

    if str_start_date and str_end_date:
        try:
            start_date = datetime.datetime.strptime(str_start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(str_end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        except ValueError:
            return "Invalid date format", 400

        orders = Order.query.filter(Order.date.between(start_date, end_date)).order_by(Order.date).all()
    else:
        orders = Order.query.order_by(Order.date).all()

    return render_template("orders.html", orders=orders, start_date=str_start_date, end_date=str_end_date)


@app.route('/send_order<int:order_id>')
@admin_only
def send_order(order_id):
    order = Order.query.get(order_id)
    order_info = f"Stated phone number: {order.phone_number}\n" \
                 f"Stated address: {order.address}\n" \
                 f"Date of order: {order.date}\n" \
                 f"Shipping price: {order.shipping_price}$\n" \
                 f"Total price: {order.total_price}$\n" \
                 f"Ordered products:\n" + "\n".join(
        [
            f"{product_assoc.product.name}({'; '.join(part.name for part in product_assoc.product.parts)}), Quantity: {product_assoc.quantity}, price: {product_assoc.quantity * product_assoc.product.price}$;"
            for product_assoc in order.products])
    user_email = order.user.email

    for product_association in ProductOrder.query.filter_by(order_id=order_id).all():
        if product_association.product.made_by_user:
            for image in product_association.product.images:
                db.session.delete(image)
            db.session.delete(product_association.product)
        db.session.delete(product_association)

    db.session.delete(order)
    db.session.commit()
    MailController().send_message("""
    Greetings!
    Your order has just been sent!
    Best regards, Shoppy\n\n ORDER DETAILS:\n""" + order_info, "Order sent", user_email)
    return redirect(url_for("orders"))


@app.route('/delete_order<int:order_id>')
@admin_only
def delete_order(order_id):
    order = Order.query.get(order_id)
    order_info = f"Stated phone number: {order.phone_number}\n" \
                 f"Stated address: {order.address}\n" \
                 f"Date of order: {order.date}\n" \
                 f"Shipping price: {order.shipping_price}$\n" \
                 f"Total price: {order.total_price}$\n" \
                 f"Ordered products:\n" + "\n".join(
        [
            f"{product_assoc.product.name}({'; '.join(part.name for part in product_assoc.product.parts)}), Quantity: {product_assoc.quantity}, price: {product_assoc.quantity * product_assoc.product.price}$;"
            for product_assoc in order.products])
    user_email = order.user.email

    for product_association in ProductOrder.query.filter_by(order_id=order_id).all():
        if product_association.product.made_by_user:
            for image in product_association.product.images:
                db.session.delete(image)
            db.session.delete(product_association.product)
        db.session.delete(product_association)

    db.session.delete(order)
    db.session.commit()
    MailController().send_message("""
        Greetings!
        Unfortunately your order has been flagged as inappropriate and has been cancelled. If you think there was an error, please let us know.
        Best regards, Shoppy\n\n ORDER DETAILS:\n""" + order_info, "Order rejected", user_email)
    return redirect(url_for("orders"))


@app.route('/generate_report')
@admin_only
def generate_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        except ValueError:
            return "Invalid date format", 400

        orders = Order.query.filter(Order.date.between(start_date, end_date)).order_by(Order.date).all()
    else:
        orders = Order.query.order_by(Order.date).all()

    report_data = io.BytesIO()
    report = xlsxwriter.Workbook(report_data)
    worksheet = report.add_worksheet()

    column_names = ["Email", "Phone Number", "Address", "Date", "Total Price", "Shipping Price", "Product",
                    "Product price", "Quantity"]
    row = 0

    for column, col_name in enumerate(column_names):
        worksheet.write(row, column, col_name)
    row += 1

    for order in orders:
        for product_assoc in order.products:
            for column, value in enumerate(
                    [order.user.email, order.phone_number, order.address, order.date, order.total_price,
                     order.shipping_price,
                     f"{product_assoc.product.name}:{[part.name for part in product_assoc.product.parts]}",
                     product_assoc.product.price,
                     product_assoc.quantity]):
                worksheet.write(row, column, value)
            row += 1

    report.close()
    report_data.seek(0)

    return send_file(report_data, as_attachment=True, download_name="Report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
