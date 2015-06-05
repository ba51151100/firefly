# coding=utf-8
from __future__ import absolute_import
from flask import request, jsonify, redirect, url_for
from flask.views import MethodView
from flask.blueprints import Blueprint
from flask_mako import render_template, render_template_def
from flask_login import login_user, current_user, login_required

from firefly.forms.user import LoginForm, RegisterForm
from firefly.models.topic import Category, Post, Comment
from firefly.models.user import User


bp = Blueprint("home", __name__, url_prefix="/")


class HomeView(MethodView):
    def get(self):
        posts = Post.objects.all()
        return render_template('index.html', posts=posts)


class CreateTopicView(MethodView):
    decorators = [login_required]

    def post(self):
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category', '')
        if category_id.isdigit():
            category_id = int(category_id)
        author_id = current_user.id
        category = Category.objects.filter(id=category_id).first()
        post = Post(title=title, content=content, category=category,
                    author=User.objects.get_or_404(id=author_id))
        post.save()
        html = render_template_def(
            '/widgets/topic_item.html', 'main', post=post, is_new=True)

        return jsonify(ok=0, html=html)


class CreateCommentView(MethodView):
    decorators = [login_required]

    def post(self):
        ref_id = request.form.get('ref_id', 0)
        content = request.form.get('content')
        author = User.objects.get_or_404(id=current_user.id)
        c = Comment(ref_id=ref_id, content=content, author=author)
        c.save()
        context = Post.objects(id=int(ref_id))
        if not context:
            context = Comment.objects(id=int(ref_id))
            if not context:
                return jsonify(ok=1, msg='not exists')
        else:
            context = context[0]
            context.comments.append(c)
            context.save()

        return jsonify(ok=0)


class LoginView(MethodView):
    def get(self):
        return redirect(url_for('home.index'))

    def post(self):
        # TODO 解决在首页登录框中无法获取 csrf_token 的问题
        form = LoginForm(csrf_enabled=False)
        if form.validate_on_submit():
            login_user(form.user)
        return redirect(url_for('home.index'))


class RegisterView(MethodView):
    def get(self):
        return redirect(url_for('home.index'))

    def post(self):
        form = RegisterForm(csrf_enabled=False)
        if form.validate_on_submit():
            user = form.save()
            login_user(user)
        return redirect(url_for('home.index'))


bp.add_url_rule('/', view_func=HomeView.as_view('index'))
bp.add_url_rule('create/topic',
                view_func=CreateTopicView.as_view('create_topic'))
bp.add_url_rule('create/comment',
                view_func=CreateCommentView.as_view('create_comment'))
bp.add_url_rule('login', view_func=LoginView.as_view('login'))
bp.add_url_rule('register', view_func=RegisterView.as_view('register'))
