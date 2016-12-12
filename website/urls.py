from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^test$', views.test_task_manager),
    url(r'^get_current_task_id$', views.get_current_task_id),
    url(r'^initialize_task$', views.initialize_task),
    url(r'^check_task_state$', views.check_task_state),
    url(r'^update_state$', views.update_state),
]
