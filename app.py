from flask import Flask, render_template, request, flash, redirect, session, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os
from hashlib import md5


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nails.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/images/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
ckeditor = CKEditor(app)


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.Integer)
    password = db.Column(db.String(100), unique=True)
    root = db.Column(db.Integer, default=0)
    order_id = db.relationship('Orders', backref='user', lazy='dynamic')

    def __repr__(self):
        return 'User %r' % self.id 


class Images(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    image_name = db.Column(db.String(500))
    description = db.Column(db.Text)

    def __repr__(self):
        return 'Image %r' % self.id 


class Articles(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.now)
    category = db.Column(db.String(100))
    text = db.Column(db.Text)
    image_name = db.Column(db.String(100))

    def __repr__(self):
        return 'Article %r' % self.id 


class Prices(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    price = db.Column(db.Integer)
    order_id = db.relationship('Orders', backref='prices', lazy='dynamic')

    def __repr__(self):
        return 'Prices %r' % self.id 


class Orders(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    id_prices = db.Column(db.Integer, db.ForeignKey('prices.id'))
    id_users = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, unique=True)

    def __repr__(self):
        return 'Prices %r' % self.id 


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    prices = Prices.query.all()
    return render_template("index.html",prices=prices)


@app.route('/articles', methods=['GET', 'POST'])
def articles():
    articles = Articles.query.order_by(Articles.date.desc()).all()
    if request.method == 'GET':
        seach = request.args.get('seach')
        if seach:
            seach= seach.capitalize()
            seach = "%{}%".format(seach)
            articles = Articles.query.filter(Articles.category.like(seach)).all()
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            image = request.files['image']
            text = request.form.get('ckeditor')
            filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid4()) + "_" + filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            
            article = Articles(title=title,category=category,text=text,image_name=pic_name)
            db.session.add(article)
            db.session.commit()
            flash("Запись добавлена!", category="ok")
            return redirect(url_for("articles"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("articles"))
    return render_template("articles.html",articles=articles)


@app.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):
    article = Articles.query.get(id)
    if not article:
        abort(404)
    return render_template("article.html", article=article)


@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    images = Images.query.order_by(Images.id.desc()).all()
    if request.method == 'POST':
        try:
            description = request.form.get('description')
            image = request.files['image']
            filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid4()) + "_" + filename
            images = Images(image_name=pic_name,description=description)
            db.session.add(images)
            db.session.commit()
            
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            flash("Изображение загружено!", category="ok")
            return redirect(url_for("gallery"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("gallery"))
    return render_template("gallery.html",images=images)


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
def profile(id):
    order_user  = Orders.query.all()
    order_user_list = []
    order_prices_list = []

    for el in order_user:
        order_user_list.append(User.query.filter_by(id=el.id_users).first())

    for el in order_user:
        order_prices_list.append(Prices.query.filter_by(id=el.id_prices).first())

   
    user = User.query.get(id)
    id_user = User.query.filter_by(email=session['name']).first().id
    if not user:
        abort(404)
    if id!=id_user:
        abort(403)
    if request.method == 'POST':
        user = User.query.filter_by(id=id).first()
        user.name = request.form.get('FullName')
        user.email = request.form.get('Email')
        user.phone_number = request.form.get('PhoneNumber')
        user.password = md5(request.form.get('password').encode()).hexdigest()
        db.session.commit()
        flash("Профиль обновлен!", category="ok")
        return redirect(url_for("profile",id=id))
    return render_template("profile.html", order_user=order_user,order_user_list=order_user_list,order_prices_list=order_prices_list,zip=zip)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    root = User.query.filter_by(email=session['name']).first().root
    if root!=1:
        abort(403)
    order_user  = Orders.query.all()
    order_user_list = []
    order_prices_list = []

    for el in order_user:
        order_user_list.append(User.query.filter_by(id=el.id_users).first())

    for el in order_user:
        order_prices_list.append(Prices.query.filter_by(id=el.id_prices).first())

   

    return render_template("admin.html",order_user=order_user,order_user_list=order_user_list,order_prices_list=order_prices_list,zip=zip)


@app.route('/servises-list', methods=['GET', 'POST'])
def servises_list():
    id_total_user = User.query.filter_by(email=session['name']).first().id
    order_user  = Orders.query.filter_by(id_users=id_total_user).all()
    order_prices_list = []
    for el in order_user:
        order_prices_list.append(Prices.query.filter_by(id=el.id_prices).first())
    return render_template("servises-list.html",zip=zip, order_user= order_user,order_prices_list=order_prices_list)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        try:
            name = request.form.get('FullName')
            phone = request.form.get('PhoneNumber')
            email = request.form.get('Email')
            password = request.form.get('password')
            user = User(name=name,email=email,phone_number=phone,password=md5(password.encode()).hexdigest())
            db.session.add(user)
            db.session.commit()
            flash("Регистрация прошла успешно!", category="ok")
            return redirect(url_for("reg"))
        except:
            flash("Произошла ошибка! Проверьте введенные данные!", category="bad")
            db.session.rollback()
            return redirect(url_for("reg"))
    return render_template("reg.html")


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        email = request.form.get('Email')
        password = md5(request.form.get('password').encode()).hexdigest()
        user = User.query.filter_by(email=email,password=password).first()
        if user:
            session['name'] = User.query.filter_by(email=email).first().email
            return redirect(url_for("index"))
        else:
            flash("Неправильная почта или пароль!", category="bad")
            return redirect(url_for("auth"))
    return render_template("auth.html")
    

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template("about.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template("contact.html")


@app.route('/pricing', methods=['GET', 'POST'])
def pricing():
    prices = Prices.query.all()
    orders = Orders.query.all()
    return render_template("pricing.html",prices=prices,orders=orders, datetime=datetime)


@app.route('/we-do', methods=['GET', 'POST'])
def we_do():
    return render_template("we-do.html")





@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    article = Articles.query.get(id)
    db.session.delete(article)
    db.session.commit()
    return redirect('/articles')


@app.route('/delete-gal/<int:id>')
def delete_gal(id):
    img = Images.query.get(id)
    db.session.delete(img)
    db.session.commit()
    return redirect('/gallery')


@app.route('/payment/<int:id>', methods=['GET', 'POST'])
def payment(id):
    if not 'name' in session:
        return redirect('/auth')
    try:
        today = datetime.now()
        date = request.form.get('date')
        time = request.form.get('time')
        full = date + "-" + time
        result = (today - datetime.strptime(date, '%Y-%m-%d')).total_seconds()
        if result>0:
            flash("Дата ("+full+") выбрана неправильно, так как этот день уже прошел!", category="bad")
            return redirect(url_for("pricing"))
        datetime_object = datetime.strptime(full, '%Y-%m-%d-%H:%M')
        id_user = User.query.filter_by(email=session['name']).first().id
        order = Orders(id_prices = id, id_users = id_user,date=datetime_object)
        db.session.add(order)
        db.session.commit()
    except:
        flash("Запись на это время невозможна!", category="bad")
        db.session.rollback()
        return redirect(url_for("pricing"))
    return redirect('/pricing')    


@app.context_processor
def inject_user():
    def get_user_name():
        if 'name' in session:
            return User.query.filter_by(email=session['name']).first()
    return dict(active_user=get_user_name())


@app.context_processor
def inject_user():
    return dict(
    category=db.session.query(Articles.category).distinct().all(),
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run(debug=True)