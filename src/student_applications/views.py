from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from q13es.forms import parse_form, FIELD_TYPES, get_pretty_answer
from q13es.models import Answer
import floppyforms as forms
import logging
import os.path

FORMS_DIR = os.path.join(os.path.dirname(__file__), 'forms')
logger = logging.getLogger(__name__)


def read_file(k):
    with open(os.path.join(FORMS_DIR, k + '.txt')) as f:
        return f.read()

CUSTOM_FIELD_TYPES = FIELD_TYPES.copy()


class ControlSelect(forms.RadioSelect):
    template_name = 'student_applications/control.html'


CUSTOM_FIELD_TYPES[_("control")] = (forms.ChoiceField, {
       'widget': ControlSelect,
       'choices': (
                   (0, _('0 - No knowledge')),
                   (1, _('1')),
                   (2, _('2 - Some knowledge')),
                   (3, _('3')),
                   (4, _('4 - Good informal knowledge or Formal Education')),
                   (5, _('5')),
                   (6, _('6 - Some parctical work experience')),
                   (7, _('7')),
                   (8, _('8 - Considerable work experience (2+ years)')),
                   (9, _('9')),
                   (10, _('10 - Full control of the technology')),
                   ),
      }
)

FORM_NAMES = (
    'personal-details',
    'about',
    'public-profiles',
    'work-experience',
    'programming-langs',
    'software-development',
    'web-technologies',
    'social-activity',
    'program',
    )

FORMS = {k: parse_form(read_file(k), CUSTOM_FIELD_TYPES) for k in FORM_NAMES}


def get_user_forms(user):
    return user.answers.values_list('q13e_slug', flat=True)


def get_user_next_form(user):

    filled = get_user_forms(user)

    for f in FORM_NAMES:
        if f not in filled:
            return f

    return None


def get_user_progress(user):
    return len(get_user_forms(user)), len(FORMS)


class ProtectedMixin(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ProtectedMixin, self).dispatch(request, *args, **kwargs)


class Dashboard(TemplateView, ProtectedMixin):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        if get_user_next_form(request.user):
            return redirect('fill_form')

        return super(Dashboard, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        d = super(Dashboard, self).get_context_data(**kwargs)

        def pretty(answer):
            d = get_pretty_answer(FORMS[a.q13e_slug], a.data)
            d['answer'] = answer
            return d

        d['answers'] = [pretty(a) for a in self.request.user.answers.all()]

        return d


class FillFormView(FormView, ProtectedMixin):
    template_name = 'fill-form.html'

    def dispatch(self, request, *args, **kwargs):
        form = self.get_form_class()
        if form is None:
            return redirect('dashboard')

        return super(FillFormView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        form_name = get_user_next_form(self.request.user)
        if not form_name:
            return None

        return FORMS[form_name]

    def form_valid(self, form):
        form_name = get_user_next_form(self.request.user)
        logger.info("User %s filled %s" % (self.request.user, form_name))
        Answer.objects.create(user=self.request.user, q13e_slug=form_name,
                              data=form.cleaned_data)
        messages.info(self.request, _("'%s' was saved.") % form.form_title)

        # TODO: save personal details in User model

        return redirect('fill_form')

    def get_context_data(self, **kwargs):
        d = super(FillFormView, self).get_context_data(**kwargs)
        d['filled_count'], d['total_count'] = get_user_progress(
                                                            self.request.user)
        d['progress'] = int(100 * (d['filled_count'] + 1) /
                             (d['total_count'] + 1))
        return d


class AllFormsView(TemplateView, ProtectedMixin):
    template_name = 'all-forms.html'

    def get_context_data(self, **kwargs):
        d = super(AllFormsView, self).get_context_data(**kwargs)
        d['forms'] = [(k, FORMS[k]) for k in FORM_NAMES]
        return d
