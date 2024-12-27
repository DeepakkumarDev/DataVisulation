from django.conf import settings 
from django.contrib import admin
from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
import re
import os 


class Customer(models.Model):
    phone = models.CharField(max_length=15)
    birth_date = models.DateField(null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name
    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name
    
    class Meta:
        ordering = ['user__first_name','user__last_name']



# class Address(models.Model):
#     street = models.CharField(max_length=255)
#     city = models.CharField(max_length=255)
#     customer = models.ForeignKey(Customer,on_delete=models.CASCADE)






def user_directory_path(instance,filename):
    return f'user_{instance.user.id}/{filename}'





class FileUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    file_name = models.FileField(upload_to=user_directory_path,validators=[FileExtensionValidator(allowed_extensions=['csv','xls'])])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name.name
    
    # def __str__(self):
    #     return f"{os.path.basename(self.file_name.name)} - {self.user.username}"


class UserTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=255, unique=True, blank=True)  # Make table_name unique
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.table_name}"



# CreateTable Model
class CreateTable(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    table_name = models.ForeignKey(UserTable, on_delete=models.CASCADE)
    file_name = models.ForeignKey(FileUpload, on_delete=models.CASCADE)
    database_table = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.table_name}"
        # return f"User: {self.user.username} - Table: {self.table_name.table_name} - File: {os.path.basename(self.file_name.file_name.name)}"



# def save(self, *args, **kwargs):
#     # Generate a unique table name if it's not already set
#     if not self.table_name:
#         # Extract the part of the email before the '@'
#         email_prefix = self.user.email.split('@')[0]
        
#         # Sanitize email_prefix to ensure it's valid as a table name (remove non-alphanumeric characters)
#         sanitized_email_prefix = re.sub(r'\W+', '_', email_prefix)  # Replace non-alphanumeric characters with '_'
        
#         # Generate a short UUID
#         unique_suffix = uuid.uuid4().hex[:8]
        
#         # Create the table name using the sanitized email prefix and unique suffix
#         self.table_name = f"table_{sanitized_email_prefix}_{unique_suffix}"
    
#     super().save(*args, **kwargs)

