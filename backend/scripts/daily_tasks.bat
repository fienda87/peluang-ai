@echo off
rem Peluang.ai daily pipeline: crawl + LLM extraction (after rate-limit reset)
cd /d C:\Users\acerr\peluang-ai\backend
if not exist logs mkdir logs
set PATH=C:\Program Files\Tesseract-OCR;%PATH%

echo ===== %DATE% %TIME% ===== >> logs\daily.log
.venv\Scripts\python.exe -m scripts.crawl_once >> logs\daily.log 2>&1
.venv\Scripts\python.exe scripts\extract_pending.py >> logs\daily.log 2>&1
echo ===== done ===== >> logs\daily.log
