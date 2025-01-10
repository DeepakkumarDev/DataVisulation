import numpy as np
import pandas as pd 
import uuid
import re
import io
import os
import random
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import FileUpload


class FillMissingColumnValueSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255, read_only=True)
    column_name = serializers.CharField(max_length=255)  # Changed to 'column_names' for clarity
    value = serializers.IntegerField()
    # fill fixed  value and value  has to be decide dynmyiclly accoridng to the columns type 
    # drop null values rows 
        
    class Meta:
        fields = ['file_name', 'column_name','value']
        
        # mean,mode,median,bfill,ffill 
        # revert 


    def update(self, instance, validated_data):
        user = self.context.get('request').user
        file_id = self.context.get('file_id')

        # Fetch the file instance based on user and file_id
        try:
            file_instance = FileUpload.objects.get(user=user, id=file_id)

            # Access the actual file path using .path from FieldFile
            file_path = file_instance.file_name.path

            if not os.path.exists(file_path):
                raise serializers.ValidationError(f"File '{file_path}' does not exist.")
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found for the given ID.")
        except Exception as e:
            raise serializers.ValidationError(f"Error accessing file: {str(e)}")

        column_name = validated_data.get('column_name')
        value = validated_data.get('value')

        try:

            df = pd.read_csv(file_path)
            if column_name not in  df.columns:
                raise serializers.ValidationError(f"column name {column_name} do not exist in the file.")

            df[column_name] = df[column_name].fillna(value)
            df.to_csv(file_path, index=False)
            return {
                "file_name": file_instance.file_name.name,
                "column_name": column_name,
                "value": f"column {column_name} have been  filled by the value {value}"
            }
        except Exception as e:
            raise serializers.ValidationError(f"Error processing the file: {str(e)}")


