from sqlalchemy.orm import relationship
from flask_login import UserMixin
from db import db

product_parts = db.Table(
    "product_parts",
    db.Column("product_id", db.Integer, db.ForeignKey("product.id")),
    db.Column("part_id", db.Integer, db.ForeignKey("part.id"))
)

characteristic_parts = db.Table(
    "characteristic_parts",
    db.Column("characteristics_id", db.Integer, db.ForeignKey("characteristics.id")),
    db.Column("part_id", db.Integer, db.ForeignKey("part.id"))
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    cart = relationship("ProductCart", back_populates="user")
    order = db.relationship("Order", back_populates="user")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    parts = db.relationship("Part", secondary=product_parts, backref="products")
    images = relationship("ProductImage", back_populates="product")
    made_by_user = db.Column(db.Boolean, nullable=False, default=False)
    users = relationship("ProductCart", back_populates="product")
    orders = relationship("ProductOrder", back_populates="product")


class ProductCart(db.Model):
    __tablename__ = "product_cart"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = relationship("Product", back_populates="users")
    user = relationship("User", back_populates="cart")


class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    category = relationship("Category", back_populates="parts")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    price = db.Column(db.Float, nullable=False)
    characteristics = db.relationship("Characteristic", secondary=characteristic_parts, backref="parts")
    images = relationship("PartImage", back_populates="part")


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parts = relationship("Part", back_populates="category")


class ProductImage(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    product = relationship("Product", back_populates="images")
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))


class PartImage(db.Model):
    __tablename__ = "part_images"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    part = relationship("Part", back_populates="images")
    part_id = db.Column(db.Integer, db.ForeignKey("part.id"))


class Characteristic(db.Model):
    __tablename__ = "characteristics"
    id = db.Column(db.Integer, primary_key=True)
    characteristic_id = db.Column(db.Integer, db.ForeignKey("characteristic_names.id"), nullable=False)
    characteristic_name = db.relationship("CharacteristicName")
    value = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"{self.characteristic_name.name}: {self.value}"


class CharacteristicName(db.Model):
    __tablename__ = "characteristic_names"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = relationship("User", back_populates="order")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    total_price = db.Column(db.Float, nullable=False, default=0)
    phone_number = db.Column(db.String, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    shipping_price = db.Column(db.Float, nullable=False)
    products = relationship("ProductOrder", back_populates="order")
    # payment_method = db.Column(db.String, nullable=False)


class ProductOrder(db.Model):
    __tablename__ = "product_order"
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = relationship("Product", back_populates="orders")
    order = relationship("Order", back_populates="products")
