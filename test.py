# This script is used to test functions without fast api
from core.analyzer import OKRAnalyzer
from utils.excel_reader import run_analysis_cli_with_description

# from utils.excel_reader import load_okrs
# from core.analyzer import OKRClassifier
# keyresults = load_okrs("assets/excel/okr.xlsx")
# lists = [okr[1] for _, okr in keyresults]
#
#
# analyzer = OKRClassifier(lists)
#
# analyzer.invoke()

kr_code = "kr11"
print(f"API called for KR: {kr_code}")
kr_info = {}
# Load full payload first
payload = run_analysis_cli_with_description(kr_code=kr_code)

kr_info["kr_name"] = [okr.description for okr in payload.okrs if okr.id == kr_code][0]
kr_info["kr_result"] = OKRAnalyzer.invoke_for_single_kr(payload, kr_code)
print(kr_info["kr_result"])
