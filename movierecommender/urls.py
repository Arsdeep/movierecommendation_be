from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/recommend/', include('recommender.urls')),
    path('api/movie/', include('moviedetail.urls')),
    path('api/search/', include('moviesearch.urls')),
]