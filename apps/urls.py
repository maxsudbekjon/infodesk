from django.urls import path, include

urlpatterns =[
    path('teachers/', include('apps.teacher.urls')),
    path('lead/',include('lead.urls'))
]