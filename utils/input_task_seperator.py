import pandas as pd

from services.openai_client import OpenAIClient
from utils.excel_reader import load_daily_task_table
from utils.extract_json_prompt import extract_json_from_response

df = pd.read_excel("../assets/excel/team tasks spreadsheet.xlsx", engine="openpyxl")
for day in df["date"].unique():
    day_tasks = load_daily_task_table(df, day)
    prompt_sys = """Your task is to process the table data below and generate a **JSON** output listing **daily tasks for each person**. Follow these rules strictly:  
   
   1. **Input Data**:  
      - The data spans multiple days (rows). Each row includes tasks for individuals like **Rezazadeh**, **Mamdoohi**, **Farmani**, etc.  
      - Tasks are listed in columns under each name, often with numbering (e.g., `1- ...`, `2- ...`) or bullet points.  
   
   2. **Output Requirements**:  
      - For **each person**, extract **all tasks** from **all rows** (days) and list them as **separate strings in an array**.  
      - **All tasks must be in Persian**, translated if necessary, and written as full sentences.  
        - Example: Convert `Scraping Google Play comments` → `جمع‌آوری نظرات Google Play`.  
        - Keep technical terms (e.g., `API`, `GitHub`, `OKR`) in English if no direct Persian equivalent exists.  
      - Split multi-part tasks (e.g., `"1- Task A 2- Task B"`) into **individual sentences**.  
      - Include **all tasks** from all days, even if repeated.  
   
   3. **Example Output**:  
      ```json  
      {  
        "rezazadeh": [  
          "پیگیری تیکت‌های مربوط به سرورهای جدید",  
          "پیگیری تیکت مربوط به تایید امنیت دسترسی به سرور FTP فراز",  
          "جلسه با تیم امنیت در خصوص پیدا کردن راه حل برای ارتباط با سرور FTP فراز",  
          "بررسی آخرین وضعیت داشبوردها از نظر آپدیت بودن و تعیین وضعیت",  
          "تدوین OKR تیم برای فصل اول 1404"  
        ],  
        "mamdoohi": [  
          "ایجاد Stored Procedure برای گزارش اقدامات",  
          "وارد کردن داده‌های Roaming",  
          "وارد کردن داده‌های Fraud Detection",  
          "جلسه با تیم امنیت"  
        ],  
        "farmani": [  
          "طراحی داشبورد مقایسه قیمت دیتا در کشورهای مختلف",  
          "بررسی دیتاهای بدست آمده و صحت سنجی آنها",  
          "جمع‌آوری اطلاعات بروی شاخص‌های مرتبط با قیمت دیتا از سایت‌های معتبر",  
          "یکپارچه‌سازی دیتاهای بدست آمده بهم نظیر ساخت دیتامدل"  
        ]  
      }  
      ```  
   
   4. **Instructions for LLM**:  
      - Parse **every row** (day) in the input table.  
      - For each person:  
        - Extract tasks from their column.  
        - Split numbered/bulleted lists into individual sentences.  
        - Translate non-Persian tasks fully into Persian.  
        - Ensure technical terms (e.g., `API`, `SQL`, `GitHub`) are retained in English if no Persian equivalent exists.  
      - Output the final result as a **single JSON object** with keys as names (lowercase, no spaces) and values as arrays of tasks.  
      - **Include all tasks** from all days, even duplicates.
   
   ### **Key Notes for LLM**:  
   - **Persian Tasks**: All tasks must be in **natural, fluent Persian**.  
   - **Splitting Tasks**: Ensure multi-part entries (e.g., `"1- Task A 2- Task B"`) are split into **separate array elements**.  
   - **Technical Terms**: Retain terms like `API`, `GitHub`, `OKR`, or translate them only if a standard Persian equivalent exists (e.g., `داده‌های Roaming` → `داده‌های رومینگ`).  
   - **Consistency**: Use consistent Persian terminology across all tasks.   """

    prompt = prompt = [
        {"role": "system", "content": (prompt_sys
                                       )},
        {"role": "user", "content": (
            "5. Input Data:\n"
            f"{day_tasks}"
        )}
    ]

    try:
        content = OpenAIClient.chat(
            prompt,
            temperature=0,  # Deterministic output
            seed=42  # Reproducibility
        )

        # Extract JSON from response using triple backticks
        data = extract_json_from_response(content)
        print(data)
    except BaseException as e:
        print(e)
    input("click")
