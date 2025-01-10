from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import FileUpload
from .serializers import FillMissingColumnValueSerializer
import os
import pandas as pd


class FillMissingColumnValueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        file_id = self.kwargs.get('pk')

        try:
            # Fetch the file instance based on user and file_id
            file_instance = FileUpload.objects.get(user=self.request.user, id=file_id)
            file_path = file_instance.file_name.path

            # Check if file exists
            if os.path.exists(file_path):
                # Read the CSV file into a DataFrame
                df = pd.read_csv(file_path)
                columns = df.columns.tolist()
                return Response({"file_name": file_instance.file_name.name, "columns": columns}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileUpload.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, *args, **kwargs):
        file_id = self.kwargs.get('pk')
        data = request.data
        context = {
            'request': request,  # Pass the request to serializer context
            'file_id': file_id  # Pass the file_id to serializer context
        }

        # Initialize serializer with the input data
        serializer = FillMissingColumnValueSerializer(data=data, context=context)
        
        # Validate serializer
        if serializer.is_valid():
            try:
                # Update the file by filling the missing values
                result = serializer.update(None, serializer.validated_data)
                return Response(result, status=status.HTTP_200_OK)
            except serializers.ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
