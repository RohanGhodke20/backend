# API Decorators Guide

This guide explains how to use the common decorators to replace try-catch blocks in your API views, making your code cleaner and more maintainable.

## Available Decorators

### 1. `@handle_api_exceptions`

**Purpose**: Automatically handles all exceptions in API views and returns standardized JSON responses.

**Benefits**:
- Eliminates repetitive try-catch blocks
- Provides consistent error responses
- Logs all exceptions with context information
- Handles both custom API exceptions and unexpected errors

**Usage**:
```python
from core.decorators import handle_api_exceptions

@handle_api_exceptions
def my_api_view(request):
    # Your view logic here - no try-catch needed!
    return Response(data)
```

**What it handles**:
- `CustomAPIException` and its subclasses
- Validation errors
- Database errors
- Unexpected exceptions
- All exceptions are logged with context

### 2. `@log_api_request`

**Purpose**: Automatically logs API requests and responses for monitoring and debugging.

**Benefits**:
- Tracks all API requests and responses
- Logs user information, method, path, and parameters
- Helps with debugging and monitoring
- No manual logging needed

**Usage**:
```python
from core.decorators import log_api_request

@log_api_request
def my_api_view(request):
    # Request and response will be automatically logged
    return Response(data)
```

**What it logs**:
- Request method and path
- User information (authenticated or anonymous)
- Query parameters
- Response status code
- View function name

### 3. `@validate_required_fields`

**Purpose**: Validates that required fields are present in request data.

**Benefits**:
- Early validation of required fields
- Consistent error messages
- Reduces boilerplate validation code
- Logs validation errors

**Usage**:
```python
from core.decorators import validate_required_fields

@validate_required_fields(['email', 'password'])
def login_view(request):
    # email and password are guaranteed to be present
    return Response(data)
```

**Parameters**:
- `required_fields` (list): List of field names that must be present in request.data

### 4. `@rate_limit_by_user`

**Purpose**: Basic rate limiting based on user (for development/testing).

**Note**: This is a simplified implementation. For production, use Django REST Framework's built-in throttling or Redis-based solutions.

**Usage**:
```python
from core.decorators import rate_limit_by_user

@rate_limit_by_user(max_requests=50, window_seconds=3600)
def my_api_view(request):
    # Rate limiting applied
    return Response(data)
```

## Combining Decorators

You can use multiple decorators together. The order matters - they execute from bottom to top:

```python
@api_view(['POST'])
@permission_classes([AllowAny])
@handle_api_exceptions      # 3. Handle any exceptions
@log_api_request           # 2. Log the request/response
@validate_required_fields(['email', 'password'])  # 1. Validate fields first
def login_view(request):
    # Your clean, focused business logic here
    return Response(data)
```

## Before vs After Examples

### Before (with try-catch):

```python
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"New user registered: {user.email}")
                return Response(
                    ResponseHandler.success(
                        message="User registered successfully",
                        data={"user_id": user.id, "email": user.email}
                    ),
                    status=status.HTTP_201_CREATED
                )
            logger.warning(f"Registration failed for email: {request.data.get('email')}")
            return Response(
                ResponseHandler.error(
                    message="Registration failed",
                    error=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                ResponseHandler.error(
                    message="Registration failed",
                    error="An unexpected error occurred"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### After (with decorators):

```python
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    @handle_api_exceptions
    @log_api_request
    @validate_required_fields(['email', 'password'])
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                ResponseHandler.success(
                    message="User registered successfully",
                    data={"user_id": user.id, "email": user.email}
                ),
                status=status.HTTP_201_CREATED
            )
        
        # If validation fails, raise an exception - decorator will handle it
        raise BadRequestException(detail=serializer.errors)
```

## Benefits of Using Decorators

1. **Cleaner Code**: Focus on business logic, not error handling boilerplate
2. **Consistency**: All views handle errors the same way
3. **Maintainability**: Error handling logic is centralized
4. **Logging**: Automatic logging of all requests and errors
5. **Validation**: Early validation of required fields
6. **DRY Principle**: No repetitive try-catch blocks

## Migration Guide

To migrate existing views to use decorators:

1. **Add imports**:
   ```python
   from core.decorators import handle_api_exceptions, log_api_request, validate_required_fields
   from core.exceptions import BadRequestException, UnauthorizedException
   ```

2. **Add decorators** to your view methods:
   ```python
   @handle_api_exceptions
   @log_api_request
   def your_method(self, request):
   ```

3. **Remove try-catch blocks** and replace with exception raising:
   ```python
   # Instead of try-catch, just raise exceptions
   if not user:
       raise UnauthorizedException(detail="Invalid credentials")
   ```

4. **Keep your business logic** clean and focused

## Best Practices

1. **Use `@handle_api_exceptions`** on all API views
2. **Use `@log_api_request`** for monitoring and debugging
3. **Use `@validate_required_fields`** for early validation
4. **Raise specific exceptions** instead of returning error responses
5. **Keep view methods focused** on business logic
6. **Use multiple decorators** when needed

## Exception Types

Use these custom exceptions for specific error cases:

- `BadRequestException` - 400 Bad Request
- `UnauthorizedException` - 401 Unauthorized  
- `NotFoundException` - 404 Not Found
- `InternalServerErrorException` - 500 Internal Server Error

Example:
```python
if not user:
    raise UnauthorizedException(detail="Invalid email or password")

if not data:
    raise BadRequestException(detail="Required data is missing")
```

This approach makes your API views much cleaner and more maintainable! 🎉 