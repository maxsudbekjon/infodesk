from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from apps.group.models.group import Group


def _update_total_student(group_pk):
    Group.objects.filter(pk=group_pk).update(
        total_student=Group.objects.get(pk=group_pk).students.exclude(
            status__in=["archived", "frozen"]
        ).count()
    )


@receiver(m2m_changed, sender=Group.students.through)
def update_group_total_student(sender, instance, action, pk_set, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    if isinstance(instance, Group):
        _update_total_student(instance.pk)
    else:
        # instance is a Student — update all affected groups
        if pk_set:
            for group_pk in pk_set:
                _update_total_student(group_pk)
