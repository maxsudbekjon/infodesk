from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.group.models.grade import Grade
from apps.group.serializers.grade import GradeModelSerializer

@extend_schema(tags=['Group'])
class GroupGradeAPIView(generics.ListAPIView):
    serializer_class = GradeModelSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        qs = Grade.objects.filter(group_id=group_id).select_related("student", "group")

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month:
            try:
                month = int(month)
            except ValueError:
                return Grade.objects.none()

            if not year:
                year = timezone.now().year
            else:
                try:
                    year = int(year)
                except ValueError:
                    return Grade.objects.none()

            qs = qs.filter(date__year=year, date__month=month)

        return qs.order_by("student__full_name", "date")
