from django.db.models import Q
from rest_framework import viewsets, permissions

from apps.group.models import GroupNote
from apps.group.permissions import IsNoteOwnerOrCEO
from apps.group.serializers import GroupNoteSerializer
from django_filters.rest_framework import DjangoFilterBackend



class GroupNoteViewSet(viewsets.ModelViewSet):
    serializer_class = GroupNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsNoteOwnerOrCEO]

    # Filtrlar
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'author']

    def get_queryset(self):
        user = self.request.user
        queryset = GroupNote.objects.select_related('group', 'author')

        if user.is_staff or hasattr(user, 'managed_branches'):
            return queryset

        if hasattr(user, 'teachers') and user.teachers is not None:
            teacher_profile = user.teachers

            return queryset.filter(
                Q(group__teacher=teacher_profile) |
                Q(group__assistant_teacher=teacher_profile)
            ).distinct()

        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)