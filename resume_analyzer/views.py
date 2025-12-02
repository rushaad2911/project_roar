# resume_analyzer/views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .core import analyze_resume_file_and_job

@login_required
@require_http_methods(["GET"])
def index(request):
    """
    Render the analyzer UI. The front-end JS will call /analyze/ to POST data.
    """
    return render(request, "resume_analyzer.html")


@login_required
@require_http_methods(["POST"])
def analyze(request):
    job_description = request.POST.get("job", "").strip()
    resume_file = request.FILES.get("resume")

    if not job_description or not resume_file:
        return JsonResponse({"error": "Please provide both the job description and resume file."}, status=400)

    try:
        result = analyze_resume_file_and_job(resume_file, job_description)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
