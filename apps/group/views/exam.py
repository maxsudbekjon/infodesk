from django.utils import timezone
from rest_framework import generics

from apps.group.models.exam import Exam
from apps.group.serializers.exam import ExamCreateSerializer, ExamListSerializer


class ExamCreateAPIView(generics.CreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamCreateSerializer


class GroupExamListAPIView(generics.ListAPIView):
    serializer_class = ExamListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        qs = Exam.objects.filter(group_id=group_id)

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month:
            try:
                month = int(month)
            except ValueError:
                return Exam.objects.none()

            if not year:
                year = timezone.now().year
            else:
                try:
                    year = int(year)
                except ValueError:
                    return Exam.objects.none()

            qs = qs.filter(date__year=year, date__month=month)

        return qs.order_by("-date", "title")
