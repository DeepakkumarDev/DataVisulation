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
from .models import FileUpload,UserTable,CreateTable,Customer

class RemoveColumnSerializer(serializers.Serializer):
    column_names = serializers.CharField(write_only=True)  # Input for column names to remove

    class Meta:
        fields = ['column_names']

    def create(self, validated_data):
        # This method should not be used since we are not creating anything.
        raise NotImplementedError("The `create` method is not supported in this serializer. Use `update` to modify the file.")

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        file_id = self.context.get('file_id')

        # Fetch the file instance based on user and file_id
        try:
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path

            if not os.path.exists(file_path):
                raise serializers.ValidationError(f"File '{file_path}' does not exist.")
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found for the given ID.")
        except Exception as e:
            raise serializers.ValidationError(f"Error accessing file: {str(e)}")

        # Extract the column names to be removed
        column_names = validated_data.get('column_names')
        column_list = re.split(r'[,\s:]+', column_names.strip())

        try:
            # Read the file into a DataFrame
            df = pd.read_csv(file_path)

            # Check if the specified columns exist
            missing_columns = [col for col in column_list if col not in df.columns]
            if missing_columns:
                raise serializers.ValidationError(f"Columns {', '.join(missing_columns)} do not exist in the file.")

            # Drop the specified columns
            df.drop(columns=column_list, inplace=True)

            # Save the updated DataFrame back to the file
            df.to_csv(file_path, index=False)

            return {
                "file_name": file_instance.file_name.name,
                "removed_columns": column_list,
                "operation": f"Columns {', '.join(column_list)} have been removed from the file '{file_instance.file_name.name}'."
            }
        except Exception as e:
            raise serializers.ValidationError(f"Error processing the file: {str(e)}")




class RenameColumnsSerializer(serializers.Serializer):
    new_column_names = serializers.DictField(
        child=serializers.CharField(),  # Each value in the dictionary will be a string (new column name)
        required=True,
        help_text="A dictionary where keys are current column names and values are new column names."
    )

    def validate_new_column_names(self, value):
        if not value:
            raise serializers.ValidationError("No columns provided for renaming.")
        return value

    class Meta:
        fields = ['new_column_names']
        
    def update(self, instance, validated_data):
        user = self.context.get('request').user
        file_id = self.context.get('file_id')
        new_column_names = validated_data.get('new_column_names', {})
        renamed_columns = []

        try:
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path

            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                for old_col, new_col in new_column_names.items():
                    if old_col in df.columns:
                        df.rename(columns={old_col: new_col}, inplace=True)
                        renamed_columns.append((old_col, new_col))
                    else:
                        raise serializers.ValidationError(f"Column '{old_col}' not found in the file")

                # Save the updated DataFrame back to the file
                df.to_csv(file_path, index=False)
                return {
                    "message": "Columns renamed successfully", 
                    "renamed_columns": renamed_columns
                }
            else:
                raise serializers.ValidationError("File not found")

        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found")
  

import numpy as np
import pandas as pd
import os
from rest_framework import serializers
from .models import FileUpload  # Assuming your FileUpload model is in the current module

import os
import pandas as pd
import numpy as np
from rest_framework import serializers
from .models import FileUpload

class ChangeDataTypeSerializer(serializers.Serializer):
    # Define a list of available data types for conversion
    dtype_mapping = [
        ('object', 'Object (String)'),
        ('int64', 'Integer (64-bit)'),
        ('int32', 'Integer (32-bit)'),
        ('int16', 'Integer (16-bit)'),
        ('int8', 'Integer (8-bit)'),
        ('float64', 'Float (64-bit)'),
        ('float32', 'Float (32-bit)'),
        ('bool', 'Boolean'),
        ('datetime64[ns]', 'Datetime'),
        ('timedelta[ns]', 'Timedelta'),
        ('category', 'Category'),
        ('string', 'String'),
        ('Int64', 'Nullable Integer (64-bit)'),
        ('Float64', 'Nullable Float (64-bit)'),
    ]

    column_name = serializers.CharField(max_length=255, help_text="Name of the column to change its data type.")
    new_data_type = serializers.ChoiceField(choices=dtype_mapping, help_text="Select the new data type for the column.")

    class Meta:
        fields = ['column_name', 'new_data_type']

    def validate(self, data):
        """
        Custom validation to ensure valid data types and valid columns.
        """
        file_id = self.context.get('file_id')
        user = self.context.get('request').user

        try:
            # Ensure the file exists
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path
            if not os.path.exists(file_path):
                raise serializers.ValidationError("The file does not exist.")

            df = pd.read_csv(file_path)
            if data['column_name'] not in df.columns:
                raise serializers.ValidationError(f"Column '{data['column_name']}' not found in the file.")
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found.")
        except Exception as e:
            raise serializers.ValidationError(f"Error while validating file: {str(e)}")
        return data

    def update(self, instance, validated_data):
        """
        Update the CSV file by changing the data type of the specified column.
        """
        user = self.context.get('request').user
        file_id = self.context.get('file_id')
        column_name = validated_data['column_name']
        new_data_type = validated_data['new_data_type']

        try:
            # Get the file instance and read the CSV file
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path

            if os.path.exists(file_path):
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Handle special cases for data type conversions
                if new_data_type == 'object':
                    # Convert the column to object (string) type
                    df[column_name] = df[column_name].astype(str)
                elif new_data_type in ['int64', 'Int64']:
                    # Convert the column to int64 or nullable Int64, handling errors
                    df[column_name] = pd.to_numeric(df[column_name], errors='coerce').astype('Int64')  # For nullable Int64
                else:
                    # General conversion for other types
                    df[column_name] = df[column_name].astype(new_data_type)

                # Save the updated DataFrame back to the file
                df.to_csv(file_path, index=False)

                return {"message": f"Data type of column '{column_name}' changed successfully to '{new_data_type}'."}
            else:
                raise serializers.ValidationError("File not found.")
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found.")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred: {str(e)}")



class FillMissingValueSerializer(serializers.Serializer):
    method = [
        ('mean', 'Mean'),
        ('median', 'Median'),
        ('mode', 'Mode'),
        ('bfill', 'Backward Fill (bfill)'),
        ('ffill', 'Forward Fill (ffill)')
    ]
    column_name = serializers.CharField(max_length=255)
    method_name = serializers.ChoiceField(choices=method)

    def update(self, instance, validated_data):
        """
        Update the CSV file by filling missing numeric values in the specified column.
        """
        user = self.context.get('request').user
        file_id = self.context.get('file_id')
        column_name = validated_data['column_name']
        method_name = validated_data['method_name']

        try:
            # Get the file instance and path
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path

            if os.path.exists(file_path):
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Check if the column exists in the dataframe
                if column_name not in df.columns:
                    raise serializers.ValidationError(f"Column '{column_name}' not found in the file.")

                # Apply the selected method to fill missing values
                if method_name == 'mean':
                    df[column_name].fillna(df[column_name].mean(), inplace=True)
                elif method_name == 'median':
                    df[column_name].fillna(df[column_name].median(), inplace=True)
                elif method_name == 'mode':
                    df[column_name].fillna(df[column_name].mode()[0], inplace=True)
                elif method_name == 'bfill':
                    df[column_name].fillna(method='bfill', inplace=True)
                elif method_name == 'ffill':
                    df[column_name].fillna(method='ffill', inplace=True)
                else:
                    raise serializers.ValidationError(f"Invalid method '{method_name}' for filling missing values.")

                # Save the updated DataFrame back to the CSV file
                df.to_csv(file_path, index=False)
                return {"message": f"Missing values in column '{column_name}' filled using '{method_name}' method."}
            else:
                raise serializers.ValidationError("File not found.")
        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found.")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred: {str(e)}")

    
class RemoveDuplicateSerializer(serializers.Serializer):
    """
    Serializer for removing duplicate rows from a CSV file.
    """
    # Specify the column(s) by which to remove duplicates (optional).
    # If no columns are provided, duplicates are removed across all columns.
    subset_columns = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_null=True, allow_empty=True
    )

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        file_id = self.context.get('file_id')
        subset_columns = validated_data.get('subset_columns', None)

        try:
            file_instance = FileUpload.objects.get(user=user, id=file_id)
            file_path = file_instance.file_name.path

            if os.path.exists(file_path):
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Remove duplicates based on the provided subset columns or entire dataframe if not provided
                if subset_columns:
                    df = df.drop_duplicates(subset=subset_columns)
                else:
                    df = df.drop_duplicates()

                # Save the updated DataFrame back to the file
                df.to_csv(file_path, index=False)

                return {"message": "Duplicates removed successfully", "remaining_rows": len(df)}
            else:
                return {"error": "File not found"}

        except FileUpload.DoesNotExist:
            raise serializers.ValidationError("File not found")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred: {str(e)}")









class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Customer 
        fields = ['id','user_id','phone','birth_date']



class BuildTableSerializer(serializers.Serializer):
    tables = serializers.ListField(child=serializers.CharField(max_length=255))


class DataCleanSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255, read_only=True)
    column_name = serializers.CharField(max_length=255)  # The column to clean
    new_column_name = serializers.CharField(max_length=255)  # New column name

    class Meta:
        fields = ['file_name', 'column_name', 'new_column_name']

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

        # Extract the column names from the request data
        column_name = validated_data.get('column_name', None)
        new_column_name = validated_data.get('new_column_name', None)

        try:
            # Read the file as a DataFrame
            df = pd.read_csv(file_path)

            # Check if the column exists before renaming
            if column_name not in df.columns:
                raise serializers.ValidationError(f"Column '{column_name}' does not exist in the file.")
            
            # Rename the column
            df.rename(columns={column_name: new_column_name}, inplace=True)

            # Save the updated DataFrame back to the same file
            with open(file_path, 'w') as f:
                df.to_csv(f, index=False)

            # Return some feedback (optional)
            return {"file_name": file_instance.file_name.name, "old_column_name": column_name, "new_column_name": new_column_name}

        except Exception as e:
            raise serializers.ValidationError(f"Error processing the file: {str(e)}")





class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload 
        fields = ["id",'file_name']

    def create(self, validated_data):
        user = self.context.get('request').user
        return FileUpload.objects.create(user=user, **validated_data)
    
    
    

class TableVisulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateTable
        fields = ['table_name']


class UserTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTable
        fields = ['table_name']

    def validate_table_name(self, value):
        user = self.context.get('request').user
        if not user:
            raise serializers.ValidationError("User is not authenticated.")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Table name can only contain letters, numbers, and underscores.")
        if UserTable.objects.filter(user=user, table_name=value).exists():
            raise serializers.ValidationError("A table with this name already exists for the user.")  
        return value

    def create(self, validated_data):
        user = self.context.get('request').user
        if not user:
            raise serializers.ValidationError("User is not authenticated.")

        table_name = validated_data.get('table_name')
        email_prefix = user.email.split('@')[0] 
        sanitized_email_prefix = re.sub(r'\W+', '_', email_prefix) 
        unique_suffix = uuid.uuid4().hex[:8]  
        unique_table_name = f"{table_name}_{sanitized_email_prefix}_{unique_suffix}"
        # unique_table_name_list = list(unique_table_name)
        # random.shuffle(unique_table_name_list)
        # unique_table_name = ''.join(unique_table_name_list)

        try:
            user_table = UserTable.objects.create(
                user=user,
                table_name=unique_table_name
            )
            return user_table
        except Exception as e:
            raise serializers.ValidationError(f"Error creating table: {str(e)}")

    def save(self, **kwargs):
        # Override the save method if necessary for custom logic (usually it's not required to override save here)
        return super().save(**kwargs)


class AppendTableSerializer(serializers.ModelSerializer):
    # class Meta:
    #     model = CreateTable  # Make sure CreateTable is your model to store the table details
    #     fields = ['table_name', 'file_name']  # Fields you want to accept in the serializer
    table_name_id = serializers.PrimaryKeyRelatedField(queryset=UserTable.objects.none(), source='table_name')
    file_name_id = serializers.PrimaryKeyRelatedField(queryset=FileUpload.objects.none(), source='file_name')

    table_name = serializers.CharField(source='table_name.table_name', read_only=True)
    file_name = serializers.CharField(source='file_name.file_name', read_only=True)

    class Meta:
        model = CreateTable
        fields = ['table_name_id', 'file_name_id', 'table_name', 'file_name', 'created_at']

    def __init__(self, *args, **kwargs):
        # Call the parent constructor
        super(AppendTableSerializer, self).__init__(*args, **kwargs)

        # Safely get the 'request' from context
        request = self.context.get('request', None)

        # If a request exists, filter the querysets based on the authenticated user
        if request and hasattr(request, 'user'):
            user = request.user
            self.fields['table_name_id'].queryset = UserTable.objects.filter(user=user)
            self.fields['file_name_id'].queryset = FileUpload.objects.filter(user=user)

    def create(self, validated_data):
        file_upload_instance = validated_data.get('file_name')
        table_name = validated_data.get('table_name')
        if not file_upload_instance:
            raise serializers.ValidationError("No file provided")

        # Access the file from the FileUpload instance and read the content
        file = file_upload_instance.file_name  # Use file_name field to access the uploaded file

        # Read the CSV file into a Pandas DataFrame
        try:
            csv_file = io.StringIO(file.read().decode())  # Read the file content into a StringIO object
            df = pd.read_csv(csv_file)  # Read CSV into DataFrame
        except Exception as e:
            raise serializers.ValidationError(f"Error reading CSV file: {str(e)}")

        # Check if the DataFrame is empty
        if df.empty:
            raise serializers.ValidationError("The uploaded CSV file is empty")

        # Check for null values in the DataFrame
        if df.isnull().values.any():
            raise serializers.ValidationError("CSV file contains null values")

        # Process the data and insert it into the table
        try:
            # Begin transaction for appending data
            with transaction.atomic():
                self.append_data_to_table(table_name, df)
        except Exception as e:
            raise serializers.ValidationError(f"Error during bulk insert: {str(e)}")

        # Return a success message or the table data
        return validated_data  # Return the validated data, or you can return a success message here.

    def append_data_to_table(self, table_name, df):
        """
        Appends data from the DataFrame into the existing table in bulk.
        """
        columns = list(df.columns)
        values = []
        data = [tuple(row) for row in df.values]

        # Prepare values for bulk insertion
        for _, row in df.iterrows():
            # Convert the row values into a tuple
            values.append(tuple(map(lambda x: x.item() if isinstance(x, np.generic) else x, row)))

        # Create the SQL query for bulk insertion
        insert_columns = ', '.join([f"`{col}`" for col in columns])
        insert_placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO `{table_name}` ({insert_columns}) VALUES ({insert_placeholders})"

        try:
            # Bulk insert using a single execute statement
            with connection.cursor() as cursor:
                cursor.executemany(insert_query, values)
                print(f"Appended {len(values)} rows into {table_name}")
        except Exception as e:
            print(f"Error while appending data into {table_name}: {str(e)}")
            raise serializers.ValidationError(f"Error appending data into table: {str(e)}")


# class CreateTableSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CreateTable
#         fields = ['table_name', 'file_name', 'created_at']

#     def create(self, validated_data):
#         """
#         Handles the creation of a table from a CSV file and stores the table in the database.
#         """
#         file_upload_instance = validated_data.get('file_name')  # Get the FileUpload instance
#         table_name = validated_data.get('table_name')

#         if not file_upload_instance:
#             raise serializers.ValidationError("No file provided")

#         # Access the file from the FileUpload instance and read the content
#         file = file_upload_instance.file_name  # Use file_name field to access the uploaded file

#         # Read the CSV file into a Pandas DataFrame
#         try:
#             csv_file = io.StringIO(file.read().decode())  # Read the file content into a StringIO object
#             df = pd.read_csv(csv_file)  # Read CSV into DataFrame
#         except Exception as e:
#             raise serializers.ValidationError(f"Error reading CSV file: {str(e)}")

#         # Check if the DataFrame is empty
#         if df.empty:
#             raise serializers.ValidationError("The uploaded CSV file is empty")

#         # Check for null values in the DataFrame
#         if df.isnull().values.any():
#             raise serializers.ValidationError("CSV file contains null values")

#         # Clean the DataFrame (you can customize this function)
#         df = self.clean_dataframe(df)

#         # Check if the table already exists
#         if self.table_exists(table_name):
#             raise serializers.ValidationError(f"Table '{table_name}' already exists in the database.")

#         # Generate the SQL to create the table from the DataFrame
#         create_table_sql= self.generate_create_table_sql_from_dataframe(table_name, df)

#         # Print the dictionary of columns and data types
#         # print("Columns and their data types:")

#         # Execute the SQL and insert data in a transaction
#         with transaction.atomic():
#             # Execute the SQL to create the table
#             self.execute_sql(create_table_sql)

#             # Insert the data into the table from the DataFrame
#             self.insert_data_from_dataframe(table_name, df)

#             # Create a CreateTable record with the database_table set to True
#             create_table_instance = CreateTable.objects.create(
#                 user=validated_data.get('user'),
#                 table_name=table_name,
#                 file_name=file_upload_instance,
#                 database_table=True
#             )
#         return create_table_instance

#     def clean_dataframe(self, df):
#         """
#         Clean the DataFrame by handling null values or any other preprocessing as required.
#         Also, convert columns to appropriate numeric types if possible.
#         """
#         # Replace NaN values with None (interpreted as NULL in SQL)
#         df = df.where(pd.notnull(df), None)
#         # Attempt to convert columns to numeric types where possible
#         for column in df.columns:
#             # Strip any unwanted characters (like commas or extra spaces) and convert to numeric if possible
#             df[column] = df[column].astype(str).str.replace(',', '').str.strip()  # Remove commas and spaces
#             df[column] = pd.to_numeric(df[column], errors='ignore')  # Convert to numeric where possible
#         return df

#     def table_exists(self, table_name):
#         """
#         Checks if the table already exists in the database.
#         """
#         with connection.cursor() as cursor:
#             cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
#             result = cursor.fetchone()
#             return result is not None

#     def generate_create_table_sql_from_dataframe(self, table_name, df):
#         column_definitions_str = ',\n'.join(self.map_dtype_to_sql(df))
#         return f'CREATE TABLE `{table_name}` ({column_definitions_str});'

#     def map_dtype_to_sql(self, df):
#         dtype_sql_mapping = {
#             'object': 'TEXT',  # Pandas object dtype (usually strings) maps to TEXT
#             'int64': 'BIGINT',  # 64-bit integers map to BIGINT
#             'int32': 'INTEGER',  # 32-bit integers map to INTEGER
#             'int16': 'INTEGER',  # 16-bit integers map to INTEGER
#             'int8': 'INTEGER',  # 8-bit integers map to INTEGER
#             'float64': 'FLOAT',  # 64-bit floating point numbers map to FLOAT
#             'float32': 'FLOAT',  # 32-bit floating point numbers map to FLOAT
#             'bool': 'BOOLEAN',  # Boolean values map to BOOLEAN
#             'datetime64[ns]': 'DATETIME',  # Pandas Timestamps map to DATETIME
#             'timedelta[ns]': 'INTERVAL',  # Pandas Timedeltas map to INTERVAL
#             'category': 'TEXT',  # Categorical data maps to TEXT
#             'string': 'TEXT',  # Pandas string type maps to TEXT
#             'Int64': 'BIGINT',  # Nullable integers map to BIGINT
#             'Float64': 'FLOAT',  # Nullable floats map to FLOAT
            
#             # NumPy specific dtypes mapping
#             np.dtype('int64').name: 'BIGINT',  # NumPy 64-bit integers map to BIGINT
#             np.dtype('int32').name: 'INTEGER',  # NumPy 32-bit integers map to INTEGER
#             np.dtype('int16').name: 'INTEGER',  # NumPy 16-bit integers map to INTEGER
#             np.dtype('int8').name: 'INTEGER',  # NumPy 8-bit integers map to INTEGER
#             np.dtype('float64').name: 'FLOAT',  # NumPy 64-bit floats map to FLOAT
#             np.dtype('float32').name: 'FLOAT',  # NumPy 32-bit floats map to FLOAT
#             np.dtype('bool').name: 'BOOLEAN',  # NumPy bools map to BOOLEAN
#         }    
#         columns = list(df.columns)
#         column_definitions = []
#         for column in columns:
#             # Get the dtype of the column
#             dtype_str = str(df[column].dtype)
#             # Check if dtype_str is in dtype_sql_mapping
#             if dtype_str in dtype_sql_mapping:
#                 # Format column definitions like: "column_name SQL_TYPE"
#                 column_definitions.append(f"`{column}` {dtype_sql_mapping[dtype_str]}")
#         print(column_definitions)
#         return column_definitions  # Return the dictionary of column names and their SQL types

#     def execute_sql(self, sql):
#         """
#         Executes the provided SQL query using Django's connection.
#         """
#         try:
#             with connection.cursor() as cursor:
#                 # Ensure using backticks for table and column names
#                 sql = sql.replace('"', '`')  # Replace double quotes with backticks
#                 cursor.execute(sql)
#                 print("Table created successfully.")
#         except Exception as e:
#             print(f"Error executing SQL: {str(e)}")
#             raise
    
#     def insert_data_from_dataframe(self, table_name, df):
#         """
#         Inserts the data from a DataFrame into the dynamically created table.
#         """
#         columns = list(df.columns)
#         for _, row in df.iterrows():
#             insert_columns = ', '.join([f"`{col}`" for col in columns])
#             insert_placeholders = ', '.join(['%s'] * len(columns))
#             try:
#                 values = tuple(map(lambda x: x.item() if isinstance(x, np.generic) else x, row))
#                 insert_query = f"INSERT INTO `{table_name}` ({insert_columns}) VALUES ({insert_placeholders})"             
#                 # Use Django's parameterized query to safely insert data
#                 with connection.cursor() as cursor:
#                     cursor.execute(insert_query, values)  # This safely passes the values as a parameter
#                     print(f"Inserted row into {table_name}: {values}")
#             except ValueError as ve:
#                 print(f"Value error while inserting data into {table_name}: {str(ve)}")
#                 raise serializers.ValidationError(f"Error inserting data into table: {str(ve)}")
#             except Exception as e:
#                 print(f"Error while inserting data into {table_name}: {str(e)}")
#                 raise serializers.ValidationError(f"Error inserting data into table: {str(e)}")

#     def format_value(self, value):
#         """
#         Formats a value based on its type to ensure it is properly inserted into the SQL query.
#         """
#         if value is None:
#             return 'NULL'  # Handle None as SQL NULL
#         elif isinstance(value, str):
#             return f"'{value}'"  # Ensure strings are wrapped in single quotes
#         elif isinstance(value, bool):
#             return 'TRUE' if value else 'FALSE'  # Convert boolean to SQL TRUE/FALSE
#         elif isinstance(value, (int, float)):
#             return value  # Return numeric values as they are, no need to convert to string
#         elif isinstance(value, pd.Timestamp):
#             return f"'{value.strftime('%Y-%m-%d')}'"  # Format datetime to SQL standard
#         else:
#             return f"'{value}'"  # Default to string if the type is unknown






import pandas as pd
import io
from django.db import transaction, connection
from rest_framework import serializers
from .models import CreateTable
import numpy as np

# class CreateTableSerializer(serializers.ModelSerializer):
#     table_name = serializers.CharField(source='table_name.table_name')
#     file_name = serializers.CharField(source='file_name.file_name')
#     class Meta:
#         model = CreateTable
#         fields = ['table_name', 'file_name', 'created_at']

from rest_framework import serializers
from .models import CreateTable, UserTable, FileUpload
from rest_framework import serializers
from .models import CreateTable, UserTable, FileUpload

class CreateTableSerializer(serializers.ModelSerializer):
    table_name_id = serializers.PrimaryKeyRelatedField(queryset=UserTable.objects.none(), source='table_name')
    file_name_id = serializers.PrimaryKeyRelatedField(queryset=FileUpload.objects.none(), source='file_name')

    table_name = serializers.CharField(source='table_name.table_name', read_only=True)
    file_name = serializers.CharField(source='file_name.file_name', read_only=True)

    class Meta:
        model = CreateTable
        fields = ['table_name_id', 'file_name_id', 'table_name', 'file_name', 'created_at']

    def __init__(self, *args, **kwargs):
        # Call the parent constructor
        super(CreateTableSerializer, self).__init__(*args, **kwargs)

        # Safely get the 'request' from context
        request = self.context.get('request', None)

        # If a request exists, filter the querysets based on the authenticated user
        if request and hasattr(request, 'user'):
            user = request.user
            self.fields['table_name_id'].queryset = UserTable.objects.filter(user=user)
            self.fields['file_name_id'].queryset = FileUpload.objects.filter(user=user)


    def create(self, validated_data):
        file_upload_instance = validated_data.get('file_name')
        table_name = validated_data.get('table_name')

        if not file_upload_instance:
            raise serializers.ValidationError("No file provided")

        # Read the file from the FileUpload instance
        file = file_upload_instance.file_name  # Assuming `file_name` is a `FileField` or similar

        try:
            csv_file = io.StringIO(file.read().decode())  # Read CSV into StringIO object
            df = pd.read_csv(csv_file)  # Read CSV into DataFrame
        except Exception as e:
            raise serializers.ValidationError(f"Error reading CSV file: {str(e)}")

        # Check if DataFrame is empty
        if df.empty:
            raise serializers.ValidationError("The uploaded CSV file is empty")

        # Clean the DataFrame (handle null values, convert columns)
        df = self.clean_dataframe(df)

        # Check if the table already exists
        if self.table_exists(table_name):
            raise serializers.ValidationError(f"Table '{table_name}' already exists in the database.")

        # Generate the SQL to create the table
        create_table_sql = self.generate_create_table_sql_from_dataframe(table_name, df)

        # Execute SQL to create the table and insert data in bulk
        with transaction.atomic():
            self.execute_sql(create_table_sql)
            self.insert_data_from_dataframe_in_bulk(table_name, df)

            # Create an entry in the CreateTable model to track the table
            create_table_instance = CreateTable.objects.create(
                user=validated_data.get('user'),
                table_name=table_name,
                file_name=file_upload_instance,
                database_table=True
            )
        return create_table_instance

    def clean_dataframe(self, df):
        """
        Clean the DataFrame by handling null values and converting columns as needed.
        """
        df = df.where(pd.notnull(df), None)
        for column in df.columns:
            df[column] = df[column].astype(str).str.replace(',', '').str.strip()
            df[column] = pd.to_numeric(df[column], errors='ignore')
        return df

    def table_exists(self, table_name):
        """
        Check if the table already exists in the database.
        """
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            return result is not None
        



    def generate_create_table_sql_from_dataframe(self, table_name, df):
        """
        Generate SQL to create the table from the DataFrame's columns and data types.
        """
        column_definitions_str = ',\n'.join(self.map_dtype_to_sql(df))
        return f'CREATE TABLE `{table_name}` ({column_definitions_str});'

    def map_dtype_to_sql(self, df):
        """
        Map pandas data types to SQL column types.
        """
        dtype_sql_mapping = {
            'object': 'TEXT',
            'int64': 'BIGINT',
            'float64': 'FLOAT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'DATETIME',
            'category': 'TEXT',
            'string': 'TEXT',
            'Int64': 'BIGINT',
            'Float64': 'FLOAT',
        }
        columns = list(df.columns)
        column_definitions = []
        for column in columns:
            dtype_str = str(df[column].dtype)
            if dtype_str in dtype_sql_mapping:
                column_definitions.append(f"`{column}` {dtype_sql_mapping[dtype_str]}")
        return column_definitions

    def execute_sql(self, sql):
        """
        Execute the SQL to create the table.
        """
        with connection.cursor() as cursor:
            sql = sql.replace('"', '`')
            cursor.execute(sql)

    def insert_data_from_dataframe_in_bulk(self, table_name, df):
        """
        Insert data into the database from the DataFrame in bulk.
        """
        # Get columns from the DataFrame
        columns = list(df.columns)
        column_names = ', '.join([f"`{col}`" for col in columns])
        placeholders = ', '.join(['%s'] * len(columns))

        # Prepare the data for bulk insertion
        data = [tuple(row) for row in df.values]

        # Insert data in bulk using Django's parameterized queries
        insert_query = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
        with connection.cursor() as cursor:
            cursor.executemany(insert_query, data)

