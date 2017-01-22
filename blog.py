"""blog.py: Multi user blog with basic blog functions."""


__author__ = 'Alan'
__copyright__ = 'Copyright 2017, Multi User Project'
__version__ = '2.0'
__status__ = 'Prototype'


# Standard library imports
import hmac
import re

# Third party imports
import webapp2
import bleach
import markdown

from webapp2 import Route
from passlib.hash import pbkdf2_sha512

# Application specific imports
from template import env
from decorator import login_required_, post_verification, comment_verification
from models import User, Post, Comment


SECRET_KEY = 'af57c5a1f269072ae4dbf097e7a35666c0d1b410d3988f6e132f128e87c6061d'


class Handler(webapp2.RequestHandler):
    """Various basic useful methods."""
    def initialize(self, *args, **kwargs):
        super(Handler, self).initialize(*args, **kwargs)
        self.uid = self.read_cookie('uid')
        self.user = self.uid and User.get_by_id(
            int(self.uid), parent=User.pk()
        )

    def write(self, *args, **kwargs):
        self.response.write(*args, **kwargs)

    def render_str(self, template, **kwargs):
        template = env.get_template(template)
        return template.render(kwargs)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

    # Cookie related functions
    def set_cookie(self, key, value):
        self.response.set_cookie(key, value, httponly=False)

    def delete_cookie(self, key):
        self.response.delete_cookie(key)

    def crypt_cookie(self, value):
        value = str(value)
        return '%s$%s' % (value, hmac.new(SECRET_KEY, value).hexdigest())

    def verify_cookie(self, cookie):
        value = cookie.split('$')[0]
        if cookie == self.crypt_cookie(value):
            return value

    def read_cookie(self, key):
        cookie = self.request.cookies.get(key)
        return cookie and self.verify_cookie(cookie)

    # Password hashing
    def crypt_pw(self, password):
        return pbkdf2_sha512.hash(password)

    def verify_pw(self, password, hashed_pw):
        return pbkdf2_sha512.verify(password, hashed_pw)


class MainPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.write('Hello, whoever it is!')


# Validate the sign up form inputs using Regular Expression.
USER_RE = re.compile(r'^[a-zA-Z0-9_-]{4,20}$')
PASS_RE = re.compile(r'^.{6,20}$')
EMAIL_RE = re.compile(r'^[\S]+@[\S]+.[\S]+$')

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)


class Signup(Handler):
    """Validate and create users' identities,
    and save them in the datastore.
    """
    def get(self):
        if self.user:
            self.redirect_to('frontpage')
        else:
            self.render('signup.html')

    def post(self):
        username = self.request.get('username').strip().title()
        password = self.request.get('password').strip()
        verify = self.request.get('verify').strip()
        email = self.request.get('email')
        signup_error = False
        context = {'username': username, 'email': email}

        if not valid_username(username):
            signup_error = True
            context.update(username_error=True)

        if not valid_password(password):
            signup_error = True
            context.update(password_error=True)
        elif password != verify:
            signup_error = True
            context.update(confirm_error=True)

        if not valid_email(email):
            signup_error = True
            context.update(email_error=True)

        if signup_error:
            self.render('signup.html', **context)
        else:
            user = User.create(username, self.crypt_pw(password), email)
            user.put()
            self.set_cookie('uid', self.crypt_cookie(user.key.id()))
            self.redirect_to('frontpage')


class Login(Handler):
    """Verify the user's identities and
    log them in upon success validation.
    """
    def get(self):
        if self.user:
            self.redirect_to('frontpage')
        else:
            self.render('login.html')

    def post(self):
        username = self.request.get('username').strip().title()
        password = self.request.get('password').strip()
        user = User.by_name(username)  # Check User existence

        if user and self.verify_pw(password, user.password):
            self.set_cookie('uid', self.crypt_cookie(user.key.id()))
            self.redirect_to('frontpage')
        else:
            self.render('login.html', login_error=True)


class Logout(Handler):
    """Log out the User by removing cookies."""
    def get(self):
        if self.user:
            self.delete_cookie('uid')

        self.redirect_to('login')


# Only retrieve the latest 10 posts
class FrontPage(Handler):
    """Front page or the home of the blog."""
    POSTS_PER_PAGE = 10

    def get(self):
        posts = Post.query_post().fetch(self.POSTS_PER_PAGE)
        context = {'posts': posts}

        if self.user:
            context.update(username=self.user.username)

        self.render('frontpage.html', **context)


# Only logged in users can access.
class NewPost(Handler):
    """Create new posts and save them in the datastore."""
    @login_required_
    def get(self):
        self.render('newpost.html', username=self.user.username)

    @login_required_
    def post(self):
        title = self.request.get('title').strip()
        excerpt = bleach.clean(self.request.get('content')[:200])
        content = bleach.clean(self.request.get('content'))
        uname = self.user.username

        if title and content:
            post = Post.create(uname, title, content, excerpt)
            post.put()
            self.redirect_to('post', pid=post.key.id())
        else:
            self.render('newpost.html', username=uname, post_error=True)


# Only user who wrote the post has access to 'Edit' feature.
# Log in is not required to enter the page.
class PostPage(Handler):
    """Permalink page of the blog posts
    where users can like, comment, and edit.
    """
    def get(self, pid):
        pid = int(pid)
        post = Post.by_id(pid)

        if not post: self.abort(404)

        comments = Comment.query_comment(Comment.pk(pid)).fetch()
        context = {'post': post, 'comments': comments}
        u = self.user

        if u:
            like = int(self.uid) in post.likes
            context.update(username=u.username, already_liked=like)

        self.render('permalink.html', **context)


# Only logged in users can comment.
class NewPostComment(Handler):
    """Create new comments and save them in the datastore."""
    @login_required_
    def post(self, pid):
        pid = int(pid)
        post = Post.by_id(pid)

        if not post: self.abort(404)

        content = bleach.clean(self.request.get('content')).replace(
            '\n', '<br>')
        u = self.user
        context = {'username': u.username, 'post': post, 'comment_error': True}

        if content:
            comment = Comment.create(pid, u.username, u.email, content)
            comment.put()
            self.redirect_to('post', pid=pid)
        else:
            self.render('editcomment.html', **context)


# Only logged in users can edit their OWN posts.
class PostEdit(Handler):
    """Edit posts and update them in the datastore."""
    @login_required_
    @post_verification
    def get(self, pid):
        post = Post.by_id(int(pid))
        self.render('editpost.html', username=self.user.username, post=post)

    @login_required_
    @post_verification
    def post(self, pid):
        pid = int(pid)
        title = self.request.get('title').strip()
        excerpt = bleach.clean(self.request.get('content')[:200])
        content = bleach.clean(self.request.get('content'))
        post = Post.by_id(pid)
        context = {
            'post': post, 'username': self.user.username, 'post_error': True
        }

        if not (title == post.title and content == post.content):
            self.redirect_to('post', pid=pid)

        if title and content:
            # User does not change the Post
            if not (title == post.title and content == post.content):
                post.title = title
                post.content = content
                post.excerpt = excerpt
                post.put()

            self.redirect_to('post', pid=pid)
        else:
            self.render('editpost.html', **context)


# Only logged in users can delete their OWN posts.
class PostDelete(Handler):
    """Post deletion.

    All the comments related to posts are deleted.
    """
    @login_required_
    @post_verification
    def post(self, pid):
        pid = int(pid)
        Post.delete_post(pid)
        Comment.delete_multi_comment(pid)
        self.redirect_to('frontpage')


# Only logged in users can edit their OWN comments.
class CommentEdit(Handler):
    """Edit comments and update them in the datastore.

    Alongside the comments, posts are retrieved to summarize
    their relationship with comments.
    """
    @login_required_
    @comment_verification
    def get(self, pid, cid):
        pid, cid = int(pid), int(cid)
        context = {
            'username': self.user.username,
            'comment': Comment.by_id(pid, cid),
            'post': Post.by_id(pid)
        }
        self.render('editcomment.html', **context)

    @login_required_
    @comment_verification
    def post(self, pid, cid):
        pid, cid = int(pid), int(cid)
        content = bleach.clean(self.request.get('content')).replace(
            '\n', '<br>')
        comment = Comment.by_id(pid, cid)
        context = {
            'username': self.user.username,
            'comment': comment,
            'post': Post.by_id(pid),
            'comment_error': True
        }

        if content:
            # User does not change the Comment
            if not content == comment.content:
                comment.content = content
                comment.put()

            self.redirect_to('post', pid=pid)
        else:
            self.render('editcomment.html', **context)


# Only logged in users are allowed for their OWN comments.
class CommentDelete(Handler):
    """Individual comment deletion."""
    @login_required_
    @comment_verification
    def post(self, pid, cid):
        pid, cid = int(pid), int(cid)
        Comment.delete_comment(pid, cid)
        self.redirect_to('post', pid=pid)


# Users can't like their OWN posts.
class PostLike(Handler):
    """Logged in users' affections for the posts."""
    @login_required_
    def post(self, pid):
        uid = int(self.uid)
        pid = int(pid)
        post = Post.by_id(pid)

        if self.user.username == post.author:
            self.abort(403)

        if not uid in post.likes:
            post.likes.append(uid)
        else:
            post.likes.remove(uid)

        post.put()
        self.redirect_to('post', pid=pid)


app = webapp2.WSGIApplication([
    Route('/signup', handler=Signup, name='signup'),
    Route('/login', handler=Login, name='login'),
    Route('/logout', handler=Logout, name='logout'),
    Route('/blog', handler=FrontPage, name='frontpage'),
    Route('/blog/newpost', handler=NewPost, name='newpost'),
    Route('/blog/<pid:\d+>', handler=PostPage, name='post'),
    Route('/blog/<pid:\d+>/edit', handler=PostEdit, name='edit'),
    Route('/blog/<pid:\d+>/delete', handler=PostDelete, name='delete'),
    Route('/blog/<pid:\d+>/comment', handler=NewPostComment, name='comment'),
    Route('/blog/<pid:\d+>/<cid:\d+>/edit', handler=CommentEdit, name='c_edit'),
    Route('/blog/<pid:\d+>/<cid:\d+>/delete', handler=CommentDelete,
          name='c_delete'),
    Route('/blog/<pid:\d+>/like', handler=PostLike, name='like'),
    Route('/', handler=MainPage),
], debug=True)
