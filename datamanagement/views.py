import csv
from django.shortcuts import render,get_object_or_404
from django.db import transaction
from django.db.models import Value
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import FileUpload,UserTable,CreateTable
from .serializers import FileUploadSerializer,UserTableSerializer,CreateTableSerializer,AppendTableSerializer,\
    DataCleanSerializer,TableVisulationSerializer,BuildTableSerializer



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def login_view(request):
    return render(request, 'registration/login.html')

def logout_view(request):
    return render(request, 'logout.html')

@login_required
def protected_page(request):
    return render(request, 'protected_page.html')
























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

class TableDetailView(APIView):    
    permission_classes = [IsAuthenticated]
    def get(self,request,pk):
        table = get_object_or_404(
            CreateTable, 
            table_name__id=pk,  # Use `table_name__id` to filter by the `id` of UserTable
            user=request.user,  # Ensure that the user is authenticated
            database_table=True  # Ensure that the table has `database_table=True`
        )
        table_name = table.table_name.table_name
        base_url = 'http://localhost:3000/d/ddqmlj39trtoga/dva'
        grafana_url = f"{base_url}?var-table={table_name}&kiosk"
        context = {
        'table_name': table_name,
        'grafana_url': grafana_url,
        }
        return render(request, 'grafana_dashboard.html', context)
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
        # Fetch a single file for the authenticated user by primary key
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
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get(self, request):
        # Fetch files for the authenticated user only
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
        # Filter the queryset to only include tables created by the authenticated user
        queryset = CreateTable.objects.filter(user=request.user)
        serializer = AppendTableSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Deserialize the incoming data and save it 
        serializer = AppendTableSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  # Save the table with the authenticated user
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
            
    


class CreateTableView(APIView):
    serializer_class = CreateTableSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get(self, request):
        # Filter the queryset to only include tables created by the authenticated user
        queryset = CreateTable.objects.filter(user=request.user)
        serializer = CreateTableSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Deserialize the incoming data and save it 
        serializer = CreateTableSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  # Save the table with the authenticated user
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
        
        
        
        # if serializer.is_valid():
        #     csv_file = serializer.validated_data['file']
        #     decoded_file = csv_file.read().decode('utf-8').splitlines()
        #     reader = csv.DictReader(decoded_file)
        #     test_results = []

        #     return Response({"message": "Batch upload successful"}, status=status.HTTP_201_CREATED)

        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





