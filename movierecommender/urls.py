from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recommender.urls')),
    path('api/', include('moviedetail.urls')),
]