from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ['user' , 'file_name' , 'created_at']
    list_select_related =['user']


@admin.register(models.UserTable)
class UserTableAdmin(admin.ModelAdmin):
    list_display = ['user' , 'table_name','created_at']
    list_select_related =['user']



@admin.register(models.CreateTable)
class CreateTableAdmin(admin.ModelAdmin):
    list_display = ['user', 'table_name',  'file_name',  'database_table',  'created_at']
    list_select_related =['user','table_name',  'file_name',]

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','phone']
    list_per_page = 10 
    list_select_related =['user']
    ordering = ['user__first_name','user__last_name']
    search_fields = ['first_name__istartswith','last_name__istartswith']
