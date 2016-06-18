from re import match

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, Count, Prefetch
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from djmail import template_mail
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from guardian.shortcuts import assign_perm, get_users_with_perms
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField

from cases.utils import get_user_model


class CaseQuerySet(QuerySet):

    def for_assign(self, user):
        content_type = ContentType.objects.get_for_model(Case)
        return self.filter(caseuserobjectpermission__permission__codename='can_view',
                           caseuserobjectpermission__permission__content_type=content_type,
                           caseuserobjectpermission__user=user)

    def for_user(self, user):
        if user.has_perm('cases.can_view_all'):
            return self
        return self.for_assign(user)

    def with_perm(self):
        return self.prefetch_related('caseuserobjectpermission_set')

    def with_record_count(self):
        return self.annotate(record_count=Count('record'))

    def with_involved_staff(self):
        qs = (CaseUserObjectPermission.objects.filter(user__is_staff=True).
              select_related('permission', 'user').
              all())
        return self.prefetch_related(Prefetch('caseuserobjectpermission_set', queryset=qs))

    def by_involved_in(self, user, by_user=True, by_group=False):
        condition = Q()
        if by_user:
            condition = condition | Q(caseuserobjectpermission__user=user)
        if by_group:
            condition = condition | Q(casegroupobjectpermission__group__user=user)
        return self.filter(condition)

    def by_msg(self, message):
        envelope = message.get_email_object().get('Envelope-To')
        result = match('^sprawa-(?P<pk>\d+)@porady.siecobywatelska.pl$', envelope)
        if result:
            return self.filter(pk=result.group('pk'))
        else:
            return self.none()

    def order_for_user(self, user, is_next):
        order = '' if is_next else '-'
        if user.is_staff:
            field_name = self.model.STAFF_ORDER_DEFAULT_FIELD
        else:
            field_name = self.model.USER_ORDER_DEFAULT_FIELD
        return self.order_by(
            '%s%s' % (order, field_name), '%spk' % order
        )


class Case(models.Model):
    STAFF_ORDER_DEFAULT_FIELD = 'last_action'
    USER_ORDER_DEFAULT_FIELD = 'last_send'
    STATUS = Choices(('0', 'free', _('free')),
                     ('1', 'assigned', _('assigned')),
                     ('2', 'closed', _('closed'))
                     )
    name = models.CharField(max_length=150, verbose_name=_("Subject"))
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='case_client', verbose_name=_("Client"))
    letter_count = models.IntegerField(default=0, verbose_name=_("Letter count"))
    last_send = models.DateTimeField(null=True, blank=True, verbose_name=_("Last send"))
    last_action = models.DateTimeField(null=True, blank=True, verbose_name=_("Last action"))
    last_received = models.DateTimeField(null=True, blank=True, verbose_name=_("Last received"))
    deadline = models.ForeignKey('events.Event',
                                 null=True,
                                 blank=True,
                                 related_name='event_deadline', verbose_name=_("Dead-line"))
    objects = CaseQuerySet.as_manager()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="case_created", verbose_name=_("Created by"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    related_name="case_modified", verbose_name=_("Modified by"))
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on"))
    handled = models.BooleanField(default=False, verbose_name=_("Handled"))
    has_project = models.BooleanField(default=False, verbose_name=_("Has project"))

    def status_display(self):
        return self.STATUS[self.status]

    def get_readed(self):
        try:
            obj = self.readed_set.all()[0]
        except IndexError:
            return False
        if obj.user.is_staff and self.last_action and self.last_action > obj.time:
            return False
        if not obj.user.is_staff and self.last_send and self.last_send > obj.time:
            return False
        return True

    def get_absolute_url(self):
        return reverse('cases:detail', kwargs={'pk': str(self.pk)})

    def get_edit_url(self):
        return reverse('cases:edit', kwargs={'pk': str(self.pk)})

    def get_users(self):
        return get_users_with_perms(self, with_group_users=False)

    def get_close_url(self):
        return reverse('cases:close', kwargs={'pk': str(self.pk)})

    def __unicode__(self):
        return self.name

    def get_email(self, user=None):
        return "%s <%s>" % (user, self.from_email) if user else self.from_email

    @property
    def from_email(self):
        return settings.PORADNIA_EMAIL_OUTPUT % self.__dict__

    @classmethod
    def get_by_email(cls, email):
        filter_param = match(settings.PORADNIA_EMAIL_INPUT, email)
        if not filter_param:
            raise cls.DoesNotExist
        return cls.objects.get(**filter_param.groupdict())

    # TODO: Remove
    def perm_check(self, user, perm):
        if not (user.has_perm('cases.' + perm) or user.has_perm('cases.' + perm, self)):
            raise PermissionDenied
        return True

    # TODO: Remove
    def view_perm_check(self, user):
        if not (user.has_perm('cases.can_view_all') or user.has_perm('cases.can_view', self)):
            raise PermissionDenied
        return True

    class Meta:
        ordering = ['last_send', ]
        permissions = (('can_view_all', _("Can view all cases")),  # Global permission
                       ('can_view', _("Can view")),
                       ('can_select_client', _("Can select client")),  # Global permission
                       ('can_assign', _("Can assign new permissions")),
                       ('can_send_to_client', _("Can send text to client")),
                       ('can_manage_permission', _("Can assign permission")),
                       ('can_add_record', _('Can add record')),
                       ('can_change_own_record', _("Can change own records")),
                       ('can_change_all_record', _("Can change all records")),
                       ('can_close_case', _("Can close case"))
                       )

    def update_handled(self):
        from letters.models import Letter
        try:
            obj = Letter.objects.case(self).filter(status='done').last()
            if obj.created_by.is_staff:
                self.handled = True
            else:
                self.handled = False
        except IndexError:
            self.handled = False
        self.save()

    def update_counters(self, save=True):
        from letters.models import Letter
        letters_list = Letter.objects.case(self)
        self.letter_count = letters_list.count()
        try:
            last_action = letters_list.last()
            self.last_action = last_action.created_on
        except IndexError:
            pass

        try:
            last_send = letters_list.last_staff_send()
            self.last_send = last_send.status_changed or last_send.created_on
        except IndexError:
            self.last_send = None

        try:
            last_received = letters_list.last_received()
            self.last_received = last_received.created_on
        except IndexError:
            self.last_received = None

        try:
            self.deadline = self.event_set.filter(deadline=True).order_by('time').all()[0]
        except IndexError:
            self.deadline = None

        if save:
            self.save()

    def status_update(self, reopen=False, save=True):
        if self.status == self.STATUS.closed and not reopen:
            return False
        content_type = ContentType.objects.get_for_model(Case)
        qs = CaseUserObjectPermission.objects.filter(permission__codename='can_send_to_client',
                                                     permission__content_type=content_type,
                                                     content_object=self,
                                                     user__is_staff=True)
        check = qs.exists()
        self.status = self.STATUS.assigned if check else self.STATUS.free
        if save:
            self.save()

    def assign_perm(self):
        assign_perm('can_view', self.created_by, self)  # assign creator
        assign_perm('can_add_record', self.created_by, self)  # assign creator
        if self.created_by.has_perm('cases.can_send_to_client'):
            assign_perm('can_send_to_client', self.created_by, self)
        if self.created_by != self.client:
            assign_perm('can_view', self.client, self)  # assign client
            assign_perm('can_add_record', self.client, self)  # assign client

    def get_next_for_user(self, user, **kwargs):
        return self.get_next_or_prev_for_user(is_next=True, user=user)

    def get_prev_for_user(self, user, **kwargs):
        return self.get_next_or_prev_for_user(is_next=False, user=user)

    def get_next_or_prev_for_user(self, is_next, user, **kwargs):
        op = 'gt' if is_next else 'lt'
        if user.is_staff:
            field_name = self.STAFF_ORDER_DEFAULT_FIELD
        else:
            field_name = self.USER_ORDER_DEFAULT_FIELD
        param = getattr(self, field_name)
        q = Q()
        if param:
            q = q | Q(**{'%s__%s' % (field_name, op): param})
        if self.pk:
            q = q | Q(**{field_name: param, 'pk__%s' % op: self.pk})
        manager = self.__class__._default_manager.using(self._state.db).filter(**kwargs)
        qs = manager.filter(q)
        qs = qs.order_for_user(user=user, is_next=is_next)
        qs = qs.for_user(user).first()


class CaseUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Case)

    def save(self, *args, **kwargs):
        super(CaseUserObjectPermission, self).save(*args, **kwargs)
        if self.permission.codename == 'can_send_to_client':
            self.content_object.status = self.content_object.STATUS.assigned
            self.content_object.save()

    def delete(self, *args, **kwargs):
        super(CaseUserObjectPermission, self).delete(*args, **kwargs)
        self.content_object.status_update()


class CaseGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Case)


limit = {'content_type__app_label': 'cases', 'content_type__model': 'case'}


class PermissionGroup(models.Model):
    name = models.CharField(max_length=25,
                            verbose_name=_("Name"))
    permissions = models.ManyToManyField(Permission,
                                         verbose_name=_("Permissions"),
                                         limit_choices_to=limit)

    def __unicode__(self):
        return self.name


def notify_new_case(sender, instance, created, **kwargs):
    if created:
        mails = template_mail.MagicMailBuilder()

        User = get_user_model()
        content_type = ContentType.objects.get_for_model(Case)
        users = User.objects.filter(user_permissions__codename='can_view_all',
                                    user_permissions__content_type=content_type).all()
        for user in users:
            email = mails.case_new(user, {'case': instance})
            email.send()

post_save.connect(notify_new_case, sender=Case, dispatch_uid="new_case_notify")


def assign_perm_new_case(sender, instance, created, **kwargs):
    if created:
        instance.assign_perm()

post_save.connect(assign_perm_new_case, sender=Case, dispatch_uid="assign_perm_new_case")
