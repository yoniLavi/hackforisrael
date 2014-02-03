"""This isn't a regular models file.
The blog entries are loaded from static markdown files in the repo

In the future, it may benefit us to implement the full model interface, but it may prove to much work
See: http://django-nonrel.org/
and: http://www.allbuttonspressed.com/blog/django/2010/04/Writing-a-non-relational-Django-backend
"""

from django.utils.translation import ugettext as _

from codecs import open  # fix opening unicode files
import datetime
import glob
import markdown
import re
import UserDict

from uni_meta import uni_meta  # our modified unicode metadata markdown extension

POSTS_PATH = "blog/posts"
# we decided that posts will be identified using a tuple of (year,month,day,slug) and the files are saved accordingly
# these three patterns below must agree with each other (and it's nicer if they agree with the urls)
POSTS_GLOB_PATTERN = "/*/*/*/*.md"
POSTS_FORMAT_PATTERN = "/%(year)s/%(month)s/%(day)s/%(slug)s.md"
POSTS_RE = re.compile(r'.*/(?P<year>\d*)/(?P<month>\d*)/(?P<day>\d*)/(?P<slug>\w*)\.md$')


class Post(object):
    """A pseudo-model for a blog post loaded from a single markdown file with its metadata"""
    def __init__(self, year, month, day, slug):  # all fields in POSTS_FORMAT_PATTERN are needed
        with open(POSTS_PATH + POSTS_FORMAT_PATTERN % locals(), encoding='utf-8') as md_file:
            md = markdown.Markdown(extensions=[uni_meta, 'codehilite'])
            html = md.convert(md_file.read())

        missing_fields = {_('author')}.difference(md.Meta)
        if missing_fields:
            raise RuntimeError("Blog post metadata is missing for '%s'. Please add: %s" % (
                               slug, ', '.join(missing_fields)))

        self.slug = slug
        self.html = html
        self.author = md.Meta[_('author')][0]
        self.hidden = md.Meta.get("hidden")  # we only care about the key here
        self.year = year
        self.month = month
        self.day = day
        self.created_date = datetime.date(self.year, self.month, self.day)


def list_post_tuples():
    posts_dir_files = glob.glob(POSTS_PATH + POSTS_GLOB_PATTERN)
    posts_matches = [POSTS_RE.match(path) for path in posts_dir_files]
    posts_dicts = [match.groupdict() for match in posts_matches if match]
    return [(int(post['year']), int(post['month']), int(post['day']), post['slug']) for post in posts_dicts]


def get_posts():
    return {post_tuple: Post(*post_tuple) for post_tuple in list_post_tuples()}


class AllPosts(UserDict.UserDict):
    """A singleton class to hold the posts lazily loaded from disk"""
    __posts = None
    __posts_for_display = None

    def __init__(self, *args, **kwargs):
        UserDict.UserDict.__init__(self)
        if not self.__posts:
            AllPosts.__posts = get_posts()

        if not self.__posts_for_display:
            AllPosts.__posts_for_display = sorted([post for post in AllPosts.__posts.values() if not post.hidden],
                                                  key=lambda x: x.created_date, reverse=True)
        self.data = AllPosts.__posts

    @staticmethod
    def get_page(num=0, size=5):
        return AllPosts.__posts_for_display[num:num+size]


#TODO: disable preloading of the posts when in development mode
