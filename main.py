from fastapi import FastAPI
from models.schemas import InputPayload, AnalysisResult
from core.analyzer import OKRAnalyzer, OKRClassifier
from utils.excel_reader import run_analysis_cli, load_okrs

from core.analyzer import OKRAnalyzer
from utils.excel_reader import run_analysis_cli, run_analysis_cli_with_description

app = FastAPI()


@app.get("/analyze", response_model=AnalysisResult)
def analyze():
    """
    Analyze team daily tasks against OKRs and return mapping of tasks to OKRs,
    along with identified risks and deliverables for each OKR.
    """
    print("api called")
    payload = run_analysis_cli()
    return OKRAnalyzer.invoke(payload)


@app.get("/analyze-kr/{kr_code}")
def analyze_kr(kr_code: str):
    """
    Analyze team daily tasks for a specific Key Result (KR) and return:
    - Tasks mapped to the KR
    - Identified risks
    - Deliverables for the KR
    """
    print(f"API called for KR: {kr_code}")
    kr_info = {}
    # Load full payload first
    payload = run_analysis_cli()

    kr_info["kr_name"] = [okr.description for okr in payload.okrs if okr.id == kr_code][0]
    kr_info["kr_result"] = OKRAnalyzer.invoke_for_single_kr(payload, kr_code)
    return kr_info


@app.get("/analyze-kr_with_description/{kr_code}")
def analyze_kr(kr_code: str):
    """
    Analyze team daily tasks for a specific Key Result (KR) and return:
    - Tasks mapped to the KR
    - Identified risks
    - Deliverables for the KR
    """
    print(f"API called for KR: {kr_code}")
    kr_info = {}
    # Load full payload first
    payload = run_analysis_cli_with_description(kr_code=kr_code)

    kr_info["kr_name"] = [okr.description for okr in payload.okrs if okr.id == kr_code][0]
    kr_info["kr_result"] = OKRAnalyzer.invoke_for_single_kr(payload, kr_code)
    return kr_info


@app.get('/kr-classifier')
def kr_classifier():
    """
    Classify the KR based on the provided input.
    """
    # Placeholder for classification logic

    # Import keyresults from excel into a dict
    okrs = load_okrs("assets/excel/okr.xlsx")
    keyresults = [okr[1] for _, okr in okrs]

    analyzer = OKRClassifier(keyresults)

    analyzer.invoke()

    return {"message": "KR classification logic goes here."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
