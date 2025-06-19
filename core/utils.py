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
        return {
            "message": message,
            "data": data if data is not None else {},
            "error": error
        } 