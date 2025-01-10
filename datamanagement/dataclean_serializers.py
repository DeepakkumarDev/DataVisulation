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





class DataOperationSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255, read_only=True)
    column_names = serializers.CharField(max_length=255)  # Changed to 'column_names' for clarity

    class Meta:
        fields = ['file_name', 'column_names']

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

        # Extract the column names to be removed from the validated data
        column_names = validated_data.get('column_names')

        # Split column names by commas, spaces, or colons, and clean up any extra spaces
        column_list = re.split(r'[,\s:]+', column_names.strip())

        try:
            # Read the file as a DataFrame
            df = pd.read_csv(file_path)

            # Check if all columns exist in the DataFrame
            missing_columns = [col for col in column_list if col not in df.columns]
            if missing_columns:
                raise serializers.ValidationError(f"Columns {', '.join(missing_columns)} do not exist in the file.")

            # Drop the specified columns
            df.drop(columns=column_list, inplace=True)

            # Save the updated DataFrame back to the same file
            df.to_csv(file_path, index=False)

            # Return feedback about the operation
            return {
                "file_name": file_instance.file_name.name,
                "removed_columns": column_list,
                "operation": f"Columns {', '.join(column_list)} have been removed from the file '{file_instance.file_name.name}'."
            }
        except Exception as e:
            raise serializers.ValidationError(f"Error processing the file: {str(e)}")






class RenameColumnSerializer(serializers.Serializer):
    """
    Serializer to handle renaming columns in the CSV file.
    """
    new_column_names = serializers.DictField(
        child=serializers.CharField(),  # Each value in the dictionary will be a string (new column name)
        required=True,
        help_text="A dictionary where keys are current column names and values are new column names."
    )

    def validate_new_column_names(self, value):
        """
        Custom validation for the new_column_names field.
        Ensures that each new column name is unique and the old column name exists in the CSV file.
        """
        if not value:
            raise serializers.ValidationError("No columns provided for renaming.")
        
        # You can add more validations here if needed, such as checking the structure of the column names
        # For instance, check if the columns are valid names (no spaces, special characters, etc.)

        return value




