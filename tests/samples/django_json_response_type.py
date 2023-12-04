from django.http import HttpResponse
import json

def foo(request):
    json_response = json.dumps({ "user_input": request.GET.get("input") })
    return HttpResponse(json_response)
