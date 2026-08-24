from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from rest_framework.authtoken.views import obtain_auth_token

def health(_request):
    return JsonResponse({'status':'ok','service':'proof'})

urlpatterns = [
    path('', include('core.web_urls')),
    path('admin/', admin.site.urls),
    path('health/', health),
    path('api/auth/token/', obtain_auth_token),
    path('api/', include('api.urls')),
]
