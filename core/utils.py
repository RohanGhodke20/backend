from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ResponseHandler:
    @staticmethod
    def success(message="Success", data=None):
        return {
            "message": message,
            "data": data if data is not None else {},
            "error": None
        }

    @staticmethod
    def error(message="Error", error=None, data=None):
        # Always return error as an object with at least a 'detail' key
        if error is None:
            error_obj = {"detail": "An error occurred."}
        elif isinstance(error, dict):
            # If already a dict, use as is (allows for extensibility)
            error_obj = error
        else:
            error_obj = {"detail": str(error)}
        return {
            "message": message,
            "data": data if data is not None else {},
            "error": error_obj
        }

class CustomPagination(PageNumberPagination):
    """
    Custom pagination class that integrates with our response format.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        Return paginated response in our standard format.
        """
        return Response({
            "message": "Data retrieved successfully",
            "data": {
                'results': data,
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.get_page_size(self.request),
            },
            "error": None
        }) 