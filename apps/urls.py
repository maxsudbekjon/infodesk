from django.urls import path, include

urlpatterns =[
    path('dashboard/', include('apps.dashboard.urls')),
    path('user/', include('apps.user.urls')),
    path('teachers/', include('apps.teacher.urls')),
    path('lead/',include('apps.lead.urls')),
    path('group/',include('apps.group.urls'))
]
