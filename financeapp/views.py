import pandas as pd
import pdfplumber
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import FinancialDocument, FinancialData

# AI Q&A
from transformers import pipeline

# Initialize Flan-T5 pipeline
qa_model = pipeline("text2text-generation", model="google/flan-t5-base")


# ---------------- Upload & Parse Financial Document ---------------- #
def upload_file(request):
    if request.method == "POST" and "file" in request.FILES:
        file = request.FILES["file"]
        doc = FinancialDocument.objects.create(file=file)

        try:
            # Excel handling
            if file.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
                for col in df.columns:
                    for val in df[col]:
                        if pd.notna(val):
                            cleaned_val = re.sub(r"^[\s\-–—]+", "", str(val))
                            FinancialData.objects.create(
                                document=doc, key=col.strip(), value=cleaned_val
                            )

            # PDF handling
            elif file.name.endswith(".pdf"):
                with pdfplumber.open(file) as pdf:
                    line_no = 1
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            for line in text.split("\n"):
                                if ":" in line:
                                    k, v = line.split(":", 1)
                                    cleaned_val = re.sub(r"^[\s\-–—]+", "", v)
                                    FinancialData.objects.create(
                                        document=doc,
                                        key=k.strip(),
                                        value=cleaned_val,
                                    )
                                else:
                                    FinancialData.objects.create(
                                        document=doc,
                                        key=f"Line {line_no}",
                                        value=line.strip(),
                                    )
                                    line_no += 1
        except Exception as e:
            FinancialData.objects.create(
                document=doc, key="Error", value=f"Failed to parse file: {str(e)}"
            )

        return redirect("dashboard", doc_id=doc.id)

    return render(request, "upload.html")


# ---------------- Dashboard & Q&A ---------------- #
def dashboard(request, doc_id):
    doc = get_object_or_404(FinancialDocument, id=doc_id)
    data = FinancialData.objects.filter(document=doc)

    context = {"data": data, "doc_id": doc.id}

    if request.method == "POST" and "question" in request.POST:
        question = request.POST.get("question")
        document_data = "\n".join([f"{item.key}: {item.value}" for item in data])

        prompt = f"""
You are a financial analyst.
Use the following financial document data to answer the question.
Document data:
{document_data[:5000]}
Question: {question}
"""

        try:
            result = qa_model(prompt, max_new_tokens=300)
            response = result[0].get("generated_text", "No answer generated.")
        except Exception as e:
            response = f"Error generating answer: {str(e)}"

        context["answer"] = response
        context["question"] = question

    return render(request, "dashboard.html", context)


# ---------------- AJAX Q&A ---------------- #
def ask_question(request, doc_id):
    if request.method == "POST":
        doc = get_object_or_404(FinancialDocument, id=doc_id)
        data = FinancialData.objects.filter(document=doc)

        question = request.POST.get("question", "")

        document_data = "\n".join([f"{item.key}: {item.value}" for item in data])

        prompt = f"""
You are a financial analyst.
Use the following financial document data to answer the question.
Document data:
{document_data[:5000]}
Question: {question}
"""

        try:
            result = qa_model(prompt, max_new_tokens=300)
            answer = result[0].get("generated_text", "No answer generated.")
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"

        return JsonResponse({"answer": answer})

    return JsonResponse({"error": "Invalid request"}, status=400)
