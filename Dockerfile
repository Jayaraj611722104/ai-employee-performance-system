FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements_mysql.txt
ENV PORT=8080
EXPOSE 8080
CMD ["gunicorn", "-b", ":8080", "app_mysql:app"]
