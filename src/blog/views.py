from django.views.generic import TemplateView
from django.http import Http404

from blog.models import AllPosts


class BlogPostListView(TemplateView):
    template_name = 'blog/post_list.html'

    #TODO add paging buttons
    def get_context_data(self, **kwargs):
        context = super(BlogPostListView, self).get_context_data(**kwargs)
        context['posts'] = AllPosts().get_page()
        return context


class BlogPostDetailView(TemplateView):
    template_name = 'blog/post_detail.html'

    def get_context_data(self, year, month, day, slug, **kwargs):
        context = super(BlogPostDetailView, self).get_context_data(**kwargs)
        context['post'] = AllPosts().get((int(year), int(month), int(day), slug))
        if not context['post']:
            raise Http404("No such post found")

        return context
