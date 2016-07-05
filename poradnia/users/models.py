# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Case, Count, IntegerField, Q, When
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from djmail.template_mail import MagicMailBuilder
from guardian.mixins import GuardianUserMixin
from guardian.utils import get_anonymous_user
from sorl.thumbnail import ImageField

from cases.models import Case as CaseModel

_('Username or e-mail')  # Hack to overwrite django translation
_('Login')


class UserQuerySet(QuerySet):

    def for_user(self, user):
        if not user.has_perm('users.can_view_other'):
            return self.filter(Q(username=user.username) | Q(is_staff=True))
        return self

    def with_case_count(self):
        return self.annotate(case_count=Count('case_client', distinct=True))

    def with_case_count_assigned(self):
        free = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.free,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        active = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.assigned,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        closed = Count(
            Case(
                When(caseuserobjectpermission__content_object__status=CaseModel.STATUS.closed,
                     then='caseuserobjectpermission__content_object__pk'),
                default=None,
                output_field=IntegerField()),
            distinct=True)

        return self.annotate(case_assigned_sum=free + active + closed,
                             case_assigned_free=free,
                             case_assigned_active=active,
                             case_assigned_closed=closed)

    def registered(self):
        user = get_anonymous_user()
        return self.exclude(pk=user.pk)


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):

    def get_by_email_or_create(self, email, notify=True):
        try:
            user = self.model.objects.get(email=email)  # Support allauth EmailAddress
        except self.model.DoesNotExist:
            user = self.register_email(email=email, notify=notify)
        return user

    def email_to_unique_username(self, email, limit=10):
        suffix_len = len(str(limit)) + 1
        max_length = User._meta.get_field('username').max_length - suffix_len
        limit_org = limit
        prefix = re.sub(r'[^A-Za-z-]', '_', email)
        prefix = prefix[:max_length]
        if not User.objects.filter(username=prefix).exists():
            return prefix
        while limit > 0:
            username = "{prefix}-{no}".format(prefix=prefix, no=limit_org - limit + 1)
            if not User.objects.filter(username=username).exists():
                return username
            limit -= 1
        raise ValueError("This email are completly creapy. I am unable to generate username")

    def register_email(self, email, notify=True, **extra_fields):
        email = self.normalize_email(email)
        password = self.make_random_password()
        username = self.email_to_unique_username(email)
        user = self.create_user(username, email, password)
        if notify:
            context = {'user': user, 'password': password}
            mails = MagicMailBuilder()
            email = mails.user_registered(email, context)
            email.send()
        return user


class User(GuardianUserMixin, AbstractUser):
    picture = ImageField(upload_to='avatars', verbose_name=_("Avatar"), null=True, blank=True)
    codename = models.CharField(max_length=15, null=True, blank=True, verbose_name=_("Codename"))
    objects = CustomUserManager()

    def get_codename(self):
        return self.codename or self.get_nicename()

    def get_nicename(self):
        if self.first_name or self.last_name:
            return self.get_full_name()
        return self.username

    def __unicode__(self):
        text = self.get_nicename()
        if self.is_staff:
            text += ' (team)'
        return text

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    class Meta:
        ordering = ['pk', ]
        permissions = (("can_view_other", "Can view other"),)
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    www = models.URLField(null=True, blank=True, verbose_name=_("Homepage"))

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
