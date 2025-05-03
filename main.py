from fastapi import FastAPI
from models.schemas import InputPayload, AnalysisResult
from core.analyzer import OKRAnalyzer
from utils.excel_reader import run_analysis_cli

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
