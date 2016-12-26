"""
This file routes URLs to handler functions.
"""

from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    # url(r'^test$', views.test),
    url(r'^get_task$', views.get_task),
    url(r'^get_container_port$', views.get_container_port),
    url(r'^initialize_task$', views.initialize_task),
    url(r'^get_filesystem$', views.get_filesystem),
    url(r'^check_task_state$', views.check_task_state),
    url(r'^update_state$', views.update_state),

    # login page
    url(r'^user_login$', views.user_login),
    url(r'^register_user$', views.register_user),
    url(r'^retrieve_access_code$', views.retrieve_access_code),

    # task session
    url(r'^.*-study_session-.*/task-.*', views.start_task),

    # admin page
    url(r'^admin', admin.site.urls),

    url(r'^', TemplateView.as_view(template_name='login.html'),
        name='home'),
]
