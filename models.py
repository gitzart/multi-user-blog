"""models.py: Google Datastore models and query related methods."""


__author__ = 'Alan'
__copyright__ = 'Copyright 2017, Multi User Project'


from google.appengine.ext import ndb


class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    created_on = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def pk(cls, group='default'):
        """Parent key of user."""
        return ndb.Key(cls, group)

    @classmethod
    def create(cls, username, password, email):
        """Create a new user to add to the datastore."""
        return cls(
            parent=cls.pk(), username=username, password=password, email=email
        )

    @classmethod
    def by_name(cls, username):
        """Query a user by name."""
        return cls.query(cls.username==username).get()


class Post(ndb.Model):
    author = ndb.StringProperty(required=True)
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    excerpt = ndb.StringProperty()
    likes = ndb.IntegerProperty(repeated=True)
    pub_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def pk(cls, name='default'):
        """Parent key of post."""
        return ndb.Key(cls, name, parent=User.pk())

    @classmethod
    def create(cls, author, title, content, excerpt, likes=[]):
        """Create a new post to add to the datastore."""
        return cls(
            parent=cls.pk(),
            author=author,
            title=title,
            content=content,
            excerpt=excerpt,
            likes=likes
        )

    @classmethod
    def by_id(cls, pid):
        """Query post by post id."""
        return cls.get_by_id(pid, parent=cls.pk())

    @classmethod
    def delete_post(cls, pid):
        """Delete individual post by post id."""
        cls.by_id(pid).key.delete()

    @classmethod
    def query_post(cls):
        """Query all the posts in the descending publishing date order."""
        return cls.query(ancestor=cls.pk()).order(-cls.pub_date)


class Comment(ndb.Model):
    author = ndb.StringProperty()
    author_email = ndb.StringProperty()
    content = ndb.TextProperty(required=True)
    pub_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def pk(cls, pid):
        """Parent key of comment."""
        return ndb.Key('Post', pid, parent=Post.pk())

    @classmethod
    def create(cls, pid, author, email, content):
        """Create a new comment to add to the datastore."""
        return cls(
            parent=cls.pk(pid),
            author=author, author_email=email, content=content
        )

    @classmethod
    def by_id(cls, pid, cid):
        """Query comment by comment id."""
        return cls.get_by_id(cid, parent=cls.pk(pid))

    @classmethod
    def delete_comment(cls, pid, cid):
        """Delete individual comment by comment id
        and the post id it belongs to.
        """
        cls.by_id(pid, cid).key.delete()

    @classmethod
    def delete_multi_comment(cls, pid):
        """Delete multiple comments by comment ids.
        and the post id they belong to.
        """
        keys = cls.query_comment(cls.pk(pid)).fetch(keys_only=True)
        if keys: ndb.delete_multi(keys)

    @classmethod
    def query_comment(cls, ancestor_key):
        """Query all the comments in the descending update date order."""
        return cls.query(ancestor=ancestor_key).order(-cls.update_date)
