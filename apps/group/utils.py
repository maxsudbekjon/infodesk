from django.db.models import Q

from apps.pupil.models.student import Student


def get_group_students_queryset(group_id):
    return Student.objects.filter(
        Q(group_id=group_id) | Q(groups__id=group_id)
    ).distinct()


def get_group_students(group):
    students_by_id = {}

    for relation_name in ("student_set", "students"):
        relation = getattr(group, relation_name, None)
        if relation is None:
            continue

        for student in relation.all():
            students_by_id[student.id] = student

    return sorted(
        students_by_id.values(),
        key=lambda student: ((student.full_name or "").lower(), student.id),
    )


def count_group_students(group):
    return len(get_group_students(group))


def build_student_image_url(student, request=None):
    image = getattr(student, "image", None)
    if not image:
        return None

    if request:
        return request.build_absolute_uri(image.url)

    return image.url
