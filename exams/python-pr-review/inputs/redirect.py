def redirect_after_login(request):
    return request.args["next"]
