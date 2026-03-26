from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response

from apps.group.models.ranking import GroupRankingComment
from apps.group.serializers.ranking import GroupRankingListSerializer
from apps.group.utils import build_student_image_url, get_group_students_queryset
from apps.pupil.models.student import Student

@extend_schema(tags=['Group'])
class GroupRankingListAPIView(generics.ListAPIView):
    serializer_class = GroupRankingListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        student_ids = get_group_students_queryset(group_id).values_list("pk", flat=True).distinct()
        qs = Student.objects.filter(pk__in=student_ids)

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        grade_filter = Q(grades__group_id=group_id)
        if month:
            try:
                month = int(month)
            except ValueError:
                return qs.none()

            if not year:
                year = timezone.now().year
            else:
                try:
                    year = int(year)
                except ValueError:
                    return qs.none()

            grade_filter &= Q(grades__date__year=year, grades__date__month=month)

        return (
            qs.annotate(
                total_grade=Coalesce(Sum("grades__grade", filter=grade_filter), 0)
            )
            .order_by("-total_grade", "full_name")
            .distinct()
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        students = page if page is not None else queryset

        student_ids = [s.id for s in students]
        comments = GroupRankingComment.objects.filter(
            group_id=self.kwargs.get("id"),
            student_id__in=student_ids,
        )
        comment_map = {c.student_id: c.comment for c in comments}

        results = []
        for idx, student in enumerate(students, start=1):
            results.append(
                {
                    "rating": idx,
                    "student": student.id,
                    "full_name": student.full_name,
                    "total_grade": student.total_grade,
                    "image": build_student_image_url(student, request=request),
                    "comment": comment_map.get(student.id),
                }
            )

        if page is not None:
            return self.get_paginated_response(results)
        return Response(results)
