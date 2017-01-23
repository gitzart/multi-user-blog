# multi-user-blog
A basic blog for multiple users

The site is live at [mub-gae.appspot.com](https://mub-gae.appspot.com/blog)

---

To run the project locally, install third party libraries. Run the following commands in the terminal.

```
$ cd /path/to/project
$ mkdir lib
$ pip install --install-option='--prefix=/path/to/project/lib' -I -r requirements.txt
$ dev_appserver.py app.yaml
```

Go to [http://localhost:8080](http://localhost:8080). That's it.

---

Note: The project is built with Google App Engine. You need to download and install it before running the above commands.

[https://cloud.google.com/appengine/docs/python/download](https://cloud.google.com/appengine/docs/python/download)
