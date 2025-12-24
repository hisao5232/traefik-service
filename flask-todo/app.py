import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# DB接続設定（環境変数から読み込み）
DB_USER = os.getenv('MYSQL_USER')
DB_PASS = os.getenv('MYSQL_PASSWORD')
DB_HOST = os.getenv('MYSQL_HOST', 'db-flask')
DB_NAME = os.getenv('MYSQL_DATABASE')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)

@app.before_request
def create_tables():
    db.create_all()

# 一覧表示
@app.route('/')
def index():
    todos = Todo.query.all()
    return render_template('index.html', todos=todos)

# タスク追加
@app.route('/add', methods=['POST'])
def add():
    task_content = request.form.get('task')
    if task_content:
        new_task = Todo(task=task_content)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

# タスク削除
@app.route('/delete/<int:id>')
def delete(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

# タスク編集（更新）
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    todo = Todo.query.get_or_404(id)
    todo.task = request.form.get('task')
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
