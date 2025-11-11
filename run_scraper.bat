@echo off
REM ===================================================
REM Script chạy scraper cho Windows Task Scheduler
REM ===================================================

REM Thay đổi đường dẫn theo project của bạn
set PROJECT_PATH=D:\Project\Data_warehouse
set PYTHON_PATH=%PROJECT_PATH%\.venv\Scripts\python.exe

REM Thay đổi ngày cần scrape (format: YYYY-MM-DD)
REM Để trống nếu muốn scrape ngày mai
set SCRAPE_DATE=

REM Chọn source: Traveloka.com, Agoda.com, hoặc Booking.com
set SOURCE_NAME=traveloka.com

REM ===================================================
REM Lấy timestamp hiện tại theo định dạng YYYYMMDD_HHMMSS (dùng cho log)
for /f %%a in ('powershell -command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set TIMESTAMP=%%a

REM Tạo thư mục log nếu chưa tồn tại
if not exist "%PROJECT_PATH%\logs" mkdir "%PROJECT_PATH%\logs"

REM Đường dẫn file log
set LOG_FILE=%PROJECT_PATH%\logs\scraper_%SOURCE_NAME%_%TIMESTAMP%.log

REM ===================================================
cd /d "%PROJECT_PATH%"

REM Ghi log và chạy scraper
(
    echo ===================================================
    echo Flight Scraper - %date% %time%
    echo ===================================================
    echo Source: %SOURCE_NAME%
    echo Date: %SCRAPE_DATE%
    echo ===================================================

    if "%SCRAPE_DATE%"=="" (
        REM Nếu không có date, scrape ngày mai
        "%PYTHON_PATH%" -m src.main -s "%SOURCE_NAME%"
    ) else (
        REM Có date, dùng date đó
        "%PYTHON_PATH%" -m src.main -s "%SOURCE_NAME%" -d "%SCRAPE_DATE%"
    )

    if %errorlevel% equ 0 (
        echo [OK] Scraping completed successfully!
    ) else (
        echo [ERROR] Scraping failed với error code: %errorlevel%
    )

    echo ===================================================
    echo Finished at %date% %time%
    echo ===================================================
) > "%LOG_FILE%" 2>&1

REM Hiển thị thông báo trên console
echo Log file: %LOG_FILE%
echo Done.
