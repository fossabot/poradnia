import django_filters
from atom.filters import CrispyFilterMixin
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from users.filters import UserChoiceFilter

from .models import Case


class NullDateRangeFilter(django_filters.DateRangeFilter):

    def __init__(self, none_label=None, *args, **kwargs):
        self.options[6] = (none_label or _('None'),
                           lambda qs, name: qs.filter(**{"%s__isnull" % name: True})
                           )
        super(NullDateRangeFilter, self).__init__(*args, **kwargs)


class CaseFilterMixin(object):

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(CaseFilterMixin, self).__init__(*args, **kwargs)


class PermissionChoiceFilter(django_filters.ModelChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(label=_("Has access by"),
                           action=lambda qs, x: qs.for_assign(x),
                           queryset=get_user_model().objects.filter(is_staff=True).all()))
        super(PermissionChoiceFilter, self).__init__(*args, **kwargs)


class StaffCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    client = UserChoiceFilter(label=_("Client"))
    permission = PermissionChoiceFilter()
    handled = django_filters.BooleanFilter(label=_("Replied"))
    status = django_filters.MultipleChoiceFilter(label=_("Status"), choices=Case.STATUS)

    def __init__(self, *args, **kwargs):
        super(StaffCaseFilter, self).__init__(*args, **kwargs)
        if not self.user.has_perm('cases.can_assign'):
            del self.filters['permission']
        self.filters['status'].field.choices.insert(0, ('', u'---------'))
        self.filters['handled'].field.widget.choices[0] = (1, _("Any state"))

    def get_order_by(self, order_choice):
        if order_choice == 'default':
            return ['-%s' % (self._meta.model.STAFF_ORDER_DEFAULT_FIELD)]
        return super(StaffCaseFilter, self).get_order_by(order_choice)

    class Meta:
        model = Case
        fields = ['id', 'status', 'client', 'name', 'has_project']
        order_by = (
            ('default', _('Default')),
            ('deadline', _('Dead-line')),
            ('pk', _('ID')),
            ('client', _('Client')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
            ('last_action', _('Last action')),
            ('last_received', _('Last received')),
        )


class UserCaseFilter(CrispyFilterMixin, CaseFilterMixin, django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Subject"), lookup_type='icontains')
    created_on = django_filters.DateRangeFilter(label=_("Created on"))
    last_send = django_filters.DateRangeFilter(label=_("Last send"))

    class Meta:
        model = Case
        fields = ['name', 'created_on', 'last_send']
        order_by = (
            ('default', _('Default')),
            ('pk', _('ID')),
            ('created_on', _('Created on')),
            ('last_send', _('Last send')),
        )

    def get_order_by(self, order_choice):
        if order_choice == 'default':
            return ['-%s' % (self._meta.model.USER_ORDER_DEFAULT_FIELD)]
        return [order_choice]
