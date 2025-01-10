import csv
import os 
import pandas as pd 
from datetime import datetime
from django.shortcuts import render,get_object_or_404
from django.db import transaction
from django.db.models import Value
from rest_framework.decorators import api_view,action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework import status
from .models import FileUpload,UserTable,CreateTable,Customer
from .serializers import FileUploadSerializer,UserTableSerializer,CreateTableSerializer,AppendTableSerializer,\
    DataCleanSerializer,TableVisulationSerializer,BuildTableSerializer,CustomerSerializer,RemoveColumnSerializer
from .dataclean_serializers import DataOperationSerializer,RenameColumnSerializer

import shutil
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Value
import os
import pandas as pd
from .models import FileUpload
from .serializers import FileUploadSerializer, RemoveColumnSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
import pandas as pd
import os
from .models import FileUpload
from .serializers import RemoveColumnSerializer,RenameColumnsSerializer,ChangeDataTypeSerializer,FillMissingValueSerializer,RemoveDuplicateSerializer






class FileUploadViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FileUpload.objects.filter(user=self.request.user).all()
        if self.request.method in ['PUT']:
            file_id = self.kwargs.get('pk') 
            columns = []
            try:
                file_instance = FileUpload.objects.get(user=self.request.user, id=file_id)
                file_path = file_instance.file_name.path
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    columns = list(df.columns)
                else:
                    return queryset.none()
            except FileUpload.DoesNotExist:
                return queryset.none()  # Return an empty queryset if file not found
            except FileNotFoundError as e:
                return queryset.annotate(column_names=Value(f"Error: {str(e)}"))
            except Exception as e:
                return queryset.annotate(column_names=Value(f"Error reading file: {str(e)}"))
            queryset = queryset.annotate(column_names=Value(', '.join(columns) if columns else "No columns found"))
        return queryset

    def get_serializer_class(self):
        if self.action == 'removecolumn':
            return RemoveColumnSerializer
        elif self.action == "renamecolumn":
            return RenameColumnsSerializer
        elif self.action == "fillmissingvalue":
            return FillMissingValueSerializer
    
        elif self.action == 'removeduplicates':
            return RemoveDuplicateSerializer
        
        elif self.action == "changedatatype":
            return ChangeDataTypeSerializer
        return FileUploadSerializer

    def get_serializer_context(self):
        # Pass file_id and request to serializer
        context = super().get_serializer_context()
        context['file_id'] = self.kwargs.get('pk')
        context['request'] = self.request
        return context

    @action(detail=True, methods=['GET', 'PUT'], url_path='removecolumn', permission_classes=[IsAuthenticated])
    def removecolumn(self, request, pk=None):
        file_upload = self.get_object()  # Get the file for the current user

        if request.method == 'GET':
            # Provide available columns for the file
            file_path = file_upload.file_name.path
            try:
                df = pd.read_csv(file_path)
                columns = df.columns.tolist()
                return Response({"column_names": columns}, status=status.HTTP_200_OK)
            except FileNotFoundError:
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == 'PUT':
            # Handle the column removal
            serializer = self.get_serializer(instance=file_upload, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            result = serializer.update(file_upload, serializer.validated_data)  # Call update explicitly
            return Response(result, status=status.HTTP_200_OK)
        
    
    @action(detail=True, methods=['GET', 'PUT'], url_path='renamecolumn', permission_classes=[IsAuthenticated])
    def renamecolumn(self, request, pk=None):
        file_upload = self.get_object()  # Get the file for the current user
        
        if request.method == 'GET':
            file_path = file_upload.file_name.path
            try:
                df = pd.read_csv(file_path)
                columns = df.columns.tolist()
                return Response({"column_names": columns}, status=status.HTTP_200_OK)
            except FileNotFoundError:
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == 'PUT':
            # Handle column renaming
            serializer = self.get_serializer(instance=file_upload, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            result = serializer.update(file_upload, serializer.validated_data)  # Call update explicitly
            return Response(result, status=status.HTTP_200_OK)
       
       
    @action(detail=True, methods=['GET', 'PUT'], url_path='changedatatype', permission_classes=[IsAuthenticated])
    def changedatatype(self, request, pk=None):
        """
        Handles changing the data types of selected columns in a CSV file.
        """
        file_upload = self.get_object()  # Get the file for the current user
        
        if request.method == 'GET':
            # Provide available columns and their current data types
            file_path = file_upload.file_name.path
            try:
                df = pd.read_csv(file_path)
                columns_with_types = {col: str(df[col].dtype) for col in df.columns}
                return Response({"columns": columns_with_types}, status=status.HTTP_200_OK)
            except FileNotFoundError:
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif request.method == 'PUT':
            # Handle changing the data types
            serializer = self.get_serializer(instance=file_upload, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            result = serializer.update(file_upload, serializer.validated_data)  # Call update explicitly
            return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET', 'PUT'], url_path='fillmissingvalue', permission_classes=[IsAuthenticated])
    def fillmissingvalue(self, request, pk=None):
        # Retrieve the file object
        file_upload = self.get_object()

        if request.method == 'GET':
            # Handle file retrieval for preview, along with column data types and missing values
            file_path = file_upload.file_name.path
            try:
                df = pd.read_csv(file_path)
                
                # Prepare column details: column name, data type, and missing values count
                column_details = []
                for column in df.columns:
                    column_info = {
                        'column_name': column,
                        'data_type': str(df[column].dtype),  # Data type of the column
                        'missing_values': int(df[column].isnull().sum())  # Count of missing values
                    }
                    column_details.append(column_info)
                
                return Response({'columns': column_details}, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            # Handle filling missing values based on user input
            serializer = self.get_serializer(instance=file_upload, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            result = serializer.update(file_upload, serializer.validated_data)  # Call update explicitly
            return Response(result, status=status.HTTP_200_OK)



    @action(detail=True, methods=['GET', 'PUT'], url_path='removeduplicates', permission_classes=[IsAuthenticated])
    def removeduplicates(self, request, pk=None):
        # Retrieve the file object
        file_upload = self.get_object()

        if request.method == 'GET':
            # Handle file retrieval for preview, along with duplicated row information
            file_path = file_upload.file_name.path
            try:
                df = pd.read_csv(file_path)

                # Find duplicated rows (across all columns)
                duplicate_rows = df[df.duplicated(keep=False)]

                # Return the number of duplicated rows and the duplicated rows themselves
                return Response(
                    {
                        "duplicated_rows": len(duplicate_rows),
                        "rows": duplicate_rows.to_dict(orient='records'),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'PUT':
            # Handle removing duplicates
            serializer = self.get_serializer(instance=file_upload, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            result = serializer.update(file_upload, serializer.validated_data)
            return Response(result, status=status.HTTP_200_OK)


    @action(detail=True, methods=['POST'], url_path='revertchanges', permission_classes=[IsAuthenticated])
    def revertchanges(self, request, pk=None):
        # Revert the file from its backup if it exists
        file_upload = self.get_object()
        file_path = file_upload.file_name.path
        backup_path = f"{file_path}.backup"

        if os.path.exists(backup_path):
            # Restore the original file from backup
            shutil.copy(backup_path, file_path)
            return Response({"message": "Changes reverted successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Backup not found, cannot revert changes."}, status=status.HTTP_400_BAD_REQUEST)




# class CustomerViewSet(CreateModelMixin,RetrieveModelMixin,UpdateModelMixin,GenericViewSet):
class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer 
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAdminUser]
    # permission_classes = [DjangoModelPermissions]
    # permission_classes =[FullDjangoModelPermissions]
    # permission_classes =[DjangoModelPermissionsOrAnonReadOnly]
    # def get_permissions(self):
    #     if self.request.method == 'GET':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    @action(detail=False,methods=['GET','PUT'],permission_classes=[IsAuthenticated])
    def me(self,request):
        # (customer,created) = Customer.objects.get_or_create(user_id=request.user.id)
        customer = Customer.objects.get(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        










class RenameColumnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        file_id = self.kwargs.get('pk')
        columns = []

        try:
            file_instance = FileUpload.objects.get(user=self.request.user, id=file_id)
            file_path = file_instance.file_name.path

            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                columns = list(df.columns)
            else:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        except FileUpload.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"columns": columns}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        file_id = self.kwargs.get('pk')
        data = request.data

        # Deserialize the data using the RenameColumnSerializer
        serializer = RenameColumnSerializer(data=data)
        if serializer.is_valid():
            new_column_names = serializer.validated_data.get('new_column_names', {})
            renamed_columns = []

            try:
                file_instance = FileUpload.objects.get(user=self.request.user, id=file_id)
                file_path = file_instance.file_name.path

                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)

                    for old_col, new_col in new_column_names.items():
                        if old_col in df.columns:
                            df.rename(columns={old_col: new_col}, inplace=True)
                            renamed_columns.append((old_col, new_col))
                        else:
                            return Response({"error": f"Column '{old_col}' not found in the file"}, status=status.HTTP_400_BAD_REQUEST)

                    # Save the updated DataFrame back to the file
                    df.to_csv(file_path, index=False)
                    return Response({"message": "Columns renamed successfully", "renamed_columns": renamed_columns}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

            except FileUpload.DoesNotExist:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataOperationViewSet(ModelViewSet):
    http_method_names = ['get', 'put', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FileUpload.objects.filter(user=self.request.user)
        if self.request.method in ['PUT', 'GET']:
            file_id = self.kwargs.get('pk') 
            columns = []
            try:
                file_instance = FileUpload.objects.get(user=self.request.user, id=file_id)
                file_path = file_instance.file_name.path
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    columns = list(df.columns)
                else:
                    return queryset.none()
            except FileUpload.DoesNotExist:
                return queryset.none()  # Return an empty queryset if file not found
            except FileNotFoundError as e:
                return queryset.annotate(column_names=Value(f"Error: {str(e)}"))
            except Exception as e:
                return queryset.annotate(column_names=Value(f"Error reading file: {str(e)}"))
            queryset = queryset.annotate(column_names=Value(', '.join(columns) if columns else "No columns found"))
        return queryset

    def get_serializer_class(self):
        if self.request.method in ['GET', 'DELETE']:
            return FileUploadSerializer
        elif self.request.method == 'PUT':
            return DataOperationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['file_id'] = self.kwargs.get('pk')  
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()  # Fetch the object instance
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response({
            "message": result.get('operation', 'Operation completed'),
            "file_name": result['file_name'],
            "removed_columns": f"Columns removed: {result['removed_columns']}"
        }, status=status.HTTP_200_OK)










class BuildTableView(APIView):
    permission_classes = [IsAuthenticated]
    """
    API View to handle the selected tables and trigger the build operation.
    """

    def get(self, request, *args, **kwargs):
        """
        GET method to return a list of available table names for the user.
        """
        # Fetch the available tables for the logged-in user where `database_table=True`
        queryset = CreateTable.objects.filter(user=request.user, database_table=True)

        # Prepare a list of table names (assuming `table_name` is a ForeignKey to `UserTable`)
        table_names = [table.table_name.table_name for table in queryset]  # Assuming `table_name` has `table_name` field
        # Return the list of available tables as JSON
        # return Response({"tables": table_names}, status=status.HTTP_200_OK)
        return render(request, 'build_form.html', {'table_names': table_names})
    def post(self, request, *args, **kwargs):
        """
        POST method to build selected tables.
        """
        serializer = BuildTableSerializer(data=request.data)
        if serializer.is_valid():
            # Extract selected tables from the request data
            selected_tables = serializer.validated_data['tables']

            # Fetch tables from the CreateTable model based on the selected table names
            tables = CreateTable.objects.filter(
                user=request.user,
                table_name__table_name__in=selected_tables  # Filter by `table_name.table_name`
            )

            # Prepare a response with the names of the tables that were built
            table_names = [table.table_name.table_name for table in tables]
            return Response({"message": "Build successful", "tables": table_names}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class TableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter the queryset to only include tables created by the authenticated user
        queryset = CreateTable.objects.filter(user=request.user,database_table=True)
        serializer =TableVisulationSerializer(queryset, many=True)
        return Response(serializer.data)



from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.timezone import datetime
from django.http import JsonResponse

class TableDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Ensure the user is authenticated
        if request.user.is_anonymous:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        # Fetch the table details for the authenticated user
        table = get_object_or_404(
            CreateTable, 
            table_name__id=pk,  # Fetch table by the primary key
            user=request.user,  # Ensure the table belongs to the authenticated user
            database_table=True  # Ensure the table has `database_table=True`
        )

        org_id = 1
        timezone = 'browser'
        
        # Make sure `table_name` exists and is not empty
        table_name = table.table_name.table_name
        if not table_name:
            return JsonResponse({"detail": "Table name is missing."}, status=400)

        # Dynamic date range
        from_time = datetime.now().isoformat()  # Replace with actual time if needed
        to_time = datetime.now().isoformat()    # Replace with actual time if needed

        # Construct the Grafana URL dynamically
        grafana_url = f'http://localhost:3000/d/ddqmlj39trtoga/data-visulation-dashboard-copysd?' \
                      f'orgId={org_id}&from={from_time}&to={to_time}&timezone={timezone}&var-table_name={table_name}'
        
        # Return the Grafana URL and other information
        return JsonResponse({
            'grafana_url': grafana_url,
            'table_name': table_name,
        })







# class TableDetailView(APIView):    
#     permission_classes = [IsAuthenticated]
#     def get(self,request,pk):
#         table = get_object_or_404(
#             CreateTable, 
#             table_name__id=pk,  # Use `table_name__id` to filter by the `id` of UserTable
#             user=request.user,  # Ensure that the user is authenticated
#             database_table=True  # Ensure that the table has `database_table=True`
#         )
#         # table_name = table.table_name.table_name
#         # base_url = 'http://localhost:3000/d/ddqmlj39trtoga/dva'
#         # grafana_url = f"{base_url}?var-table={table_name}&kiosk"

#         org_id = 1
#         timezone = 'browser'
        
#         # Example: you can pass dynamic values based on user selection or logic
#         table_name = 'dataecom_deepak_dev_mca22_du_fd126d99'
        
#         # Optional: Dynamic date range
#         from_time = datetime.now().isoformat()  # Replace with actual time if needed
#         to_time = datetime.now().isoformat()    # Replace with actual time if needed
        
#         # Build the Grafana URL dynamically
#         grafana_url = f'http://localhost:3000/d/ddqmlj39trtoga/data-visulation-dashboard-copysd?' \
#                     f'orgId={org_id}&from={from_time}&to={to_time}&timezone={timezone}&var-table_name={table_name}'
    

#         context = {
#         'table_name': table_name,
#         'grafana_url': grafana_url,
#         }
#         return render(request, 'grafana_dashboard.html', context)
        # return Response(context)
    
        

def grafana_dashboard(request, table_name):
    base_url = 'http://localhost:3000/d/ddqmlj39trtoga/nighwantech'
    # grafana_url = f"{base_url}?var-tablename={table_name}&kiosk=tv"
    grafana_url = f"{base_url}?var-tablename={table_name}&kiosk"
    # Check if the user is an admin
    edit_url = None
    if request.user.is_staff:  # Assuming is_staff is used to identify admins
        edit_url = f"http://localhost:3000/dashboards"
        print(f"Admin user detected, edit URL: {edit_url}")

    context = {
        'table_name': table_name,
        'grafana_url': grafana_url,
        'edit_url': edit_url
    }
    print(f"Context: {context}")  # Debug statement to check the context
    return render(request, 'data/grafana_dashboard.html', context)





class DataCleanViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put','delete']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = FileUpload.objects.filter(user=self.request.user)
        if self.request.method == 'PUT' or self.request.method == 'GET':
            # Annotate with a blank 'column_name' for display purposes
            queryset = queryset.annotate(column_name=Value(''),new_column_name=Value(''))

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET' or self.request.method == 'DELETE':
            return FileUploadSerializer
        elif self.request.method == 'POST':
            return FileUploadSerializer
        elif self.request.method == 'PUT':
            return DataCleanSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['file_id'] = self.kwargs.get('pk')  # 'pk' is the file ID from the URL
        context['request'] = self.request
        return context



    def update(self, request, *args, **kwargs):
        # Get the instance to update
        user = request.user        
        if user.is_anonymous:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        instance = self.get_object()
        # Use DataCleanSerializer to handle the incoming data
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        # Call the update method of the serializer
        cleaned_column = serializer.save()

        return Response({
            "message": f"Data cleaned for column: {cleaned_column}"
        }, status=status.HTTP_200_OK)



 

class DataCleanView(APIView):
    serializer_class = DataCleanSerializer
    permission_classes = [IsAuthenticated]


    def get(self, request, pk):
        try:
            file = FileUpload.objects.get(user=request.user, pk=pk)
        except FileUpload.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a dict where `column_name` is annotated with None
        annotated_file = {
            'file_name': file.file_name,
            'column_name': None  # Since column_name is not part of the model, we set it to None
        }

        # Serialize the annotated file data
        serializer = DataCleanSerializer([annotated_file])

        return Response(serializer.data)
    def put(self, request, pk, *args, **kwargs):
        # Fetch a single file for the authenticated user by primary key
        try:
            file = FileUpload.objects.get(user=request.user, pk=pk)
        except FileUpload.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a dict where `column_name` is annotated with None
        annotated_file = {
            'file_name': file.file_name,
            'column_name': None  # We set column_name as None
        }

        # Deserialize the incoming request data (including column_name)
        serializer = DataCleanSerializer([annotated_file], data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Call the save method to perform the data processing
        mean_value = serializer.save()

        # Return the cleaned data with the calculated mean
        return Response({
            "mean_value": mean_value,
            "column_name": serializer.validated_data['column_name']
        }, status=status.HTTP_200_OK)
    



class UserTableView(APIView):
    serializer_class = UserTableSerializer
    permission_classes = [IsAuthenticated] 

    def get(self,request):
        queryset = UserTable.objects.filter(user=request.user)
        serializer = UserTableSerializer(queryset,many=True)
        return Response(serializer.data)

    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class FileUploadView(APIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]  
    def get(self, request):
        queryset = FileUpload.objects.filter(user=request.user)
        serializer = FileUploadSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AppendDataView(APIView):
    serializer_class = AppendTableSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = CreateTable.objects.filter(user=request.user)
        serializer = AppendTableSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppendTableSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
            
    


class CreateTableView(APIView):
    serializer_class = CreateTableSerializer
    permission_classes = [IsAuthenticated]  
    def get(self, request):
        queryset = CreateTable.objects.filter(user=request.user).select_related('table_name','file_name')
        serializer = CreateTableSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateTableSerializer(data=request.data, context={'request': request})
        # serializer = CreateTableSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
        
        
        
        # if serializer.is_valid():
        #     csv_file = serializer.validated_data['file']
        #     decoded_file = csv_file.read().decode('utf-8').splitlines()
        #     reader = csv.DictReader(decoded_file)
        #     test_results = []

        #     return Response({"message": "Batch upload successful"}, status=status.HTTP_201_CREATED)

        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





