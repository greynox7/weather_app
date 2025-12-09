# Python 3.10 슬림 버전 사용 (가볍고 안정적)
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 8000번 열기
EXPOSE 8000

# Gunicorn으로 서버 실행 (프로덕션용)
# -w 4: 워커 프로세스 4개 사용
# -b 0.0.0.0:8000: 8000번 포트로 외부 접속 허용
# main:app : main.py 파일의 app 객체를 실행
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
