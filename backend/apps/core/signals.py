"""
FRS §3.5 / §6.1 audit trail signals for selected tables.

Deliberately per-sender receivers (not a single global receiver matching on
`sender in (...)`) so Django only dispatches these for the exact models
we care about, rather than firing — and paying the membership-check cost —
on every save in the system.

Actor attribution: most of the audited events already have an obvious
actor field on the instance itself (Certificate.issued_by/revoked_by). For
the rest (User creation via walk-in/admin, User/Enrollment deletion,
Enrollment suspension) the calling code explicitly sets a transient
`instance._audit_actor` before saving/deleting — the same explicit-actor
convention already used throughout this codebase (e.g.
Application._record_transition(changed_by=...)) rather than inferring the
current user from request-local state.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.certificates.models import Certificate
from apps.enrollments.models import Enrollment

from .models import AuditLog

User = get_user_model()

USER_WATCHED_FIELDS = ["role", "is_active", "ec_number"]


def _capture_old(instance, fields):
    old = {}
    if instance.pk:
        try:
            row = type(instance).objects.get(pk=instance.pk)
            old = {f: getattr(row, f) for f in fields}
        except type(instance).DoesNotExist:
            old = {}
    instance._audit_old = old


def _log_field_diffs(instance, fields, actor, notes_prefix):
    old = getattr(instance, "_audit_old", None)
    if not old:
        return
    for field in fields:
        old_val = old.get(field)
        new_val = getattr(instance, field, None)
        if old_val != new_val:
            AuditLog.log(
                actor=actor, action=AuditLog.Action.UPDATE, instance=instance,
                field_name=field, old_value=old_val, new_value=new_val,
                notes=f"{notes_prefix}.{field} changed",
            )


# ── User: create / update (role, is_active, ec_number) / delete ───────────

@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    _capture_old(instance, USER_WATCHED_FIELDS)


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    actor = getattr(instance, "_audit_actor", None)
    if created:
        AuditLog.log(
            actor=actor, action=AuditLog.Action.CREATE, instance=instance,
            notes=f"User created (role={instance.role})",
        )
        return
    _log_field_diffs(instance, USER_WATCHED_FIELDS, actor, "User")


@receiver(post_delete, sender=User)
def user_post_delete(sender, instance, **kwargs):
    actor = getattr(instance, "_audit_actor", None)
    AuditLog.log(
        actor=actor, action=AuditLog.Action.DELETE, instance=instance,
        notes=f"User deleted: {instance.email}",
    )


# ── Certificate: create / revoke ────────────────────────────────────────

@receiver(pre_save, sender=Certificate)
def certificate_pre_save(sender, instance, **kwargs):
    _capture_old(instance, ["is_revoked"])


@receiver(post_save, sender=Certificate)
def certificate_post_save(sender, instance, created, **kwargs):
    if created:
        AuditLog.log(
            actor=instance.issued_by, action=AuditLog.Action.CREATE, instance=instance,
            notes=f"Certificate issued: {instance.certificate_number}",
        )
        return
    _log_field_diffs(instance, ["is_revoked"], instance.revoked_by, "Certificate")


@receiver(post_delete, sender=Certificate)
def certificate_post_delete(sender, instance, **kwargs):
    actor = getattr(instance, "_audit_actor", None)
    AuditLog.log(
        actor=actor, action=AuditLog.Action.DELETE, instance=instance,
        notes=f"Certificate deleted: {instance.certificate_number}",
    )


# ── Enrollment: suspend / reinstate / delete ────────────────────────────

@receiver(pre_save, sender=Enrollment)
def enrollment_pre_save(sender, instance, **kwargs):
    _capture_old(instance, ["is_suspended"])


@receiver(post_save, sender=Enrollment)
def enrollment_post_save(sender, instance, created, **kwargs):
    if created:
        return
    actor = getattr(instance, "_audit_actor", None)
    _log_field_diffs(instance, ["is_suspended"], actor, "Enrollment")


@receiver(post_delete, sender=Enrollment)
def enrollment_post_delete(sender, instance, **kwargs):
    actor = getattr(instance, "_audit_actor", None)
    AuditLog.log(
        actor=actor, action=AuditLog.Action.DELETE, instance=instance,
        notes=f"Enrollment deleted for application {instance.application_id}",
    )
