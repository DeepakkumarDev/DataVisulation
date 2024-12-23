from django.urls import path ,include
from .import views
from rest_framework.routers import DefaultRouter 

router = DefaultRouter()
router.register('data-clean',views.DataCleanViewSet,basename='data-clean')


urlpatterns = [
    path('',include(router.urls)),
    path('upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('table/',views.UserTableView.as_view(),name='user-table'),
    path('create-table/',views.CreateTableView.as_view(),name='table-view'),
    path('append-data/',views.AppendDataView.as_view(),name='append-data'),
    path('data-clean/<int:pk>/',views.DataCleanView.as_view(),name='data-clean'),
    path('visulaize/',views.TableView.as_view(),name='table-list'),
    path('visulaize/<int:pk>/',views.TableDetailView.as_view() ,name='table-detail'),
    path('build-table/', views.BuildTableView.as_view(), name='build-table'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('protected/', views.protected_page, name='protected'),

]