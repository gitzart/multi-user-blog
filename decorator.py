"""decorator.py: Useful decorator functions for multi user blog."""


__author__ = 'Alan'
__copyright__ = 'Copyright 2017, Multi User Project'


from models import Post, Comment


def login_required_(handler_method):
    """A decorator to require that a user be logged in to access a handler.

    Note: This decorator is the modified version of the original webapp2
    'login_required' function.

    It works on any HTTP Verbs.
    """
    def check_login(self, *args, **kwargs):
        if not self.user:
            self.redirect_to('login')
        else:
            handler_method(self, *args, **kwargs)

    return check_login


def post_verification(handler_method):
    """A decorator to verify that a post exists
    and a user is the owner of the post to access a handler.
    """
    def verify_post(self, *args, **kwargs):
        post = Post.by_id(int(kwargs.get('pid')))

        if not post: self.abort(404)
        if self.user.username != post.author: self.abort(403)

        handler_method(self, *args, **kwargs)

    return verify_post


def comment_verification(handler_method):
    """A decorator to verify that a comment exists
    and a user is the owner of the comment to access a handler.
    """
    def verify_comment(self, *args, **kwargs):
        pid, cid = int(kwargs.get('pid')), int(kwargs.get('cid'))
        comment = Comment.by_id(pid, cid)

        if not comment: self.abort(404)
        if self.user.username != comment.author: self.abort(403)

        handler_method(self, *args, **kwargs)

    return verify_comment
