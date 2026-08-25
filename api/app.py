from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import base64
from datetime import datetime

# Vercel executes this file from /api. The templates and static folders are
# one level above it, so use absolute paths instead of Flask's default paths.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static'
)

SECRET_KEY = os.environ.get('SECRET_KEY')
MONGODB_URI = os.environ.get('MONGODB_URI')

if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable is required')
if not MONGODB_URI:
    raise RuntimeError('MONGODB_URI environment variable is required')

app.secret_key = SECRET_KEY

# Keep the MongoDB client lazy. Do not perform database queries while the
# Vercel module is importing; doing so can make a cold start fail before Flask
# can handle the request.
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    retryWrites=True
)
db = client.get_default_database()

dogs_collection = db.dogs
settings_collection = db.settings
admin_collection = db.admin


def initialize_database():
    """Create the small amount of default data the first time it is needed."""
    if admin_collection.count_documents({}) == 0:
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            raise RuntimeError('ADMIN_PASSWORD environment variable is required')

        admin_collection.insert_one({
            'username': os.environ.get('ADMIN_USERNAME', 'admin'),
            'password': generate_password_hash(admin_password)
        })

    if settings_collection.count_documents({}) == 0:
        settings_collection.insert_one({
            'site_name': '浦城仁爱流浪动物救助基地',
            'description': '成立基地的目的是为了救助被遗弃或走失的猫狗，让流浪毛孩子得以远离饥寒病痛，拥有一个安稳栖息之所。',
            'wechat': '',
            'phone': '',
            'address': '福建省南平市浦城县',
            'about': '愿善意传递不息，人间温情长存，欢迎更多爱心人士加入，共同守护世间每一只可爱的小生命！我们有专人负责爱心资金管理，每一项收支都会公布，确保每一分钱都花在毛孩子身上，不辜负爱心人士的信任！',
            'donation_note': '目前基地通过微信群接受爱心捐助，所有款项100%用于毛孩子的食物、医疗和日常照料。欢迎加入我们的救助群，共同监督。'
        })


@app.before_request
def ensure_database():
    # Only initialize when a request actually reaches the function.
    # This avoids a MongoDB network operation during Vercel cold-start import.
    initialize_database()


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # Keep the real exception visible in Vercel logs while returning a useful
    # response instead of an opaque FUNCTION_INVOCATION_FAILED page.
    app.logger.exception('Unhandled application error')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return '服务器暂时无法处理请求，请稍后再试。', 500


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def parse_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def image_to_base64(file):
    data = file.read()
    content_type = file.content_type or 'application/octet-stream'
    return 'data:' + content_type + ';base64,' + base64.b64encode(data).decode()


# ========== 前台 ==========

@app.route('/')
def index():
    settings = settings_collection.find_one() or {}
    dogs = list(
        dogs_collection.find({'status': 'available'}).sort('createdAt', -1)
    )
    return render_template('index.html', settings=settings, dogs=dogs)


@app.route('/dog/<dog_id>')
def dog_detail(dog_id):
    object_id = parse_object_id(dog_id)
    if object_id is None:
        return redirect(url_for('index'))

    settings = settings_collection.find_one() or {}
    dog = dogs_collection.find_one({'_id': object_id})

    if not dog:
        return redirect(url_for('index'))

    other_dogs = list(
        dogs_collection.find({
            '_id': {'$ne': object_id},
            'status': 'available'
        }).limit(4)
    )

    return render_template(
        'dog_detail.html',
        settings=settings,
        dog=dog,
        other_dogs=other_dogs
    )


@app.route('/donate')
def donate():
    settings = settings_collection.find_one() or {}
    return render_template('donate.html', settings=settings)


@app.route('/about')
def about():
    settings = settings_collection.find_one() or {}
    return render_template('about.html', settings=settings)


# ========== API ==========

@app.route('/api/dogs')
def api_dogs():
    dogs = list(
        dogs_collection.find({'status': 'available'}).sort('createdAt', -1)
    )
    for dog in dogs:
        dog['_id'] = str(dog['_id'])
    return jsonify(dogs)


@app.route('/api/dog/<dog_id>')
def api_dog(dog_id):
    object_id = parse_object_id(dog_id)
    if object_id is None:
        return jsonify({'error': 'Invalid dog id'}), 400

    dog = dogs_collection.find_one({'_id': object_id})
    if dog:
        dog['_id'] = str(dog['_id'])
        return jsonify(dog)
    return jsonify({'error': 'Not found'}), 404


# ========== 后台 ==========

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        admin = admin_collection.find_one({'username': username})

        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))

        flash('用户名或密码错误', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():
    dogs = list(dogs_collection.find().sort('createdAt', -1))
    for dog in dogs:
        dog['_id'] = str(dog['_id'])

    stats = {
        'total': dogs_collection.count_documents({}),
        'available': dogs_collection.count_documents({'status': 'available'}),
        'adopted': dogs_collection.count_documents({'status': 'adopted'})
    }

    return render_template('admin/dashboard.html', dogs=dogs, stats=stats)


@app.route('/admin/dog/add', methods=['GET', 'POST'])
@login_required
def admin_add_dog():
    if request.method == 'POST':
        photo_base64 = ''
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            photo_base64 = image_to_base64(photo_file)

        now = datetime.now()
        dogs_collection.insert_one({
            'name': request.form.get('name', '').strip(),
            'age': request.form.get('age', '').strip(),
            'gender': request.form.get('gender', ''),
            'breed': request.form.get('breed', '').strip(),
            'personality': request.form.get('personality', '').strip(),
            'health': request.form.get('health', '').strip(),
            'story': request.form.get('story', '').strip(),
            'status': request.form.get('status', 'available'),
            'photo': photo_base64,
            'createdAt': now,
            'updatedAt': now
        })

        flash('狗狗添加成功！', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/dog_form.html', dog=None)


@app.route('/admin/dog/edit/<dog_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_dog(dog_id):
    object_id = parse_object_id(dog_id)
    if object_id is None:
        flash('狗狗不存在', 'error')
        return redirect(url_for('admin_dashboard'))

    dog = dogs_collection.find_one({'_id': object_id})
    if not dog:
        flash('狗狗不存在', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name', '').strip(),
            'age': request.form.get('age', '').strip(),
            'gender': request.form.get('gender', ''),
            'breed': request.form.get('breed', '').strip(),
            'personality': request.form.get('personality', '').strip(),
            'health': request.form.get('health', '').strip(),
            'story': request.form.get('story', '').strip(),
            'status': request.form.get('status', 'available'),
            'updatedAt': datetime.now()
        }

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            update_data['photo'] = image_to_base64(photo_file)

        dogs_collection.update_one({'_id': object_id}, {'$set': update_data})
        flash('狗狗信息更新成功！', 'success')
        return redirect(url_for('admin_dashboard'))

    dog['_id'] = str(dog['_id'])
    return render_template('admin/dog_form.html', dog=dog)


@app.route('/admin/dog/delete/<dog_id>', methods=['POST'])
@login_required
def admin_delete_dog(dog_id):
    object_id = parse_object_id(dog_id)
    if object_id is not None:
        dogs_collection.delete_one({'_id': object_id})
    flash('狗狗已删除', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = settings_collection.find_one() or {}

    if request.method == 'POST':
        update_data = {
            'site_name': request.form.get('site_name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'wechat': request.form.get('wechat', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'about': request.form.get('about', '').strip(),
            'donation_note': request.form.get('donation_note', '').strip()
        }

        qr_file = request.files.get('donation_qr')
        if qr_file and qr_file.filename:
            update_data['donation_qr'] = image_to_base64(qr_file)

        if settings:
            settings_collection.update_one(
                {'_id': settings['_id']},
                {'$set': update_data}
            )
        else:
            settings_collection.insert_one(update_data)

        flash('设置已保存', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html', settings=settings)


@app.route('/admin/change-password', methods=['POST'])
@login_required
def admin_change_password():
    current = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    admin = admin_collection.find_one({
        'username': session.get('admin_username')
    })

    if not admin or not check_password_hash(admin['password'], current):
        flash('当前密码错误', 'error')
    elif new_password != confirm:
        flash('两次输入的新密码不一致', 'error')
    elif len(new_password) < 6:
        flash('新密码至少6位', 'error')
    else:
        admin_collection.update_one(
            {'username': session.get('admin_username')},
            {'$set': {'password': generate_password_hash(new_password)}}
        )
        flash('密码修改成功', 'success')

    return redirect(url_for('admin_settings'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
