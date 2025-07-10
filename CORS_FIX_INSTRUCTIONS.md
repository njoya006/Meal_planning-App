# ChopSmo CORS Fix Instructions

You're encountering a CORS issue with your frontend at https://frontendsmo.vercel.app trying to access your backend at https://njoya.pythonanywhere.com.

## Error Description
```
Access to fetch at 'https://njoya.pythonanywhere.com/api/users/login/' from origin 'https://frontendsmo.vercel.app' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## What's Happening
While you have CORS settings configured in your Django settings.py, there's an issue with the preflight OPTIONS requests not being properly handled for the login endpoint. This is a common issue on PythonAnywhere hosting where the standard Django CORS headers middleware doesn't always work as expected.

## Solution
We've prepared a comprehensive fix that includes:

1. A custom CORS middleware that explicitly adds CORS headers to responses
2. Updates to the UserLoginView to handle OPTIONS preflight requests
3. Updates to the settings.py to include the custom middleware

## Files Modified Locally
1. Created `meal_project/custom_cors_middleware.py` - A custom middleware to ensure CORS headers are added
2. Modified `meal_project/settings.py` - Added the custom middleware to the middleware stack
3. Updated `users/views.py` - Added explicit CORS headers to the login view and added OPTIONS method handler

## How to Apply These Changes on PythonAnywhere

### Option 1: Using our prepared script
1. Upload `fix_cors_pythonanywhere.py` to your PythonAnywhere account
2. Open a PythonAnywhere console
3. Navigate to your project directory (e.g., `cd ~/ChopSmo`)
4. Run: `python fix_cors_pythonanywhere.py`
5. Go to the Web tab and reload your web app

### Option 2: Manual updates
1. Create a new file at `meal_project/custom_cors_middleware.py` on PythonAnywhere with the custom middleware code
2. Update your `meal_project/settings.py` to import and use the custom middleware
3. Update your `users/views.py` to handle OPTIONS requests and add explicit CORS headers

## Testing the Fix
After applying the changes:
1. Upload and run `check_cors_settings.py` to verify your CORS configuration
2. Check if your frontend at https://frontendsmo.vercel.app can successfully log in

## Additional Notes
- This fix specifically addresses the login endpoint issue
- The custom middleware is designed to only add headers for requests from your frontend domains
- If you still encounter issues, check the PythonAnywhere error logs
- Consider testing with browser developer tools (Network tab) to see the headers being sent/received

These changes should resolve the CORS issues with your frontend accessing the backend login endpoint.
