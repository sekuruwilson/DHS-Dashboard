from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-panel/', include('indicators.admin_urls')),
    path('', RedirectView.as_view(url='/admin-panel/', permanent=False)),
]
