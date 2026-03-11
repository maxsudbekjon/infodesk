from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response

from apps.group.models.ranking import GroupRankingComment
from apps.group.serializers.ranking import GroupRankingListSerializer
from apps.pupil.models.student import Student

@extend_schema(tags=['Group'])
class GroupRankingListAPIView(generics.ListAPIView):
    serializer_class = GroupRankingListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        qs = Student.objects.filter(groups__id=group_id)

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        grade_filter = Q(grades__group_id=group_id)
        if month:
            try:
                month = int(month)
            except ValueError:
                return Student.objects.none()

            if not year:
                year = timezone.now().year
            else:
                try:
                    year = int(year)
                except ValueError:
                    return Student.objects.none()

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
                    "comment": comment_map.get(student.id),
                }
            )

        if page is not None:
            return self.get_paginated_response(results)
        return Response(results)
