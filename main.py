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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
