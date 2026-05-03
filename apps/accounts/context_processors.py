def user_role(request):
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'user_branch': request.user.branch,
        }
    return {}
