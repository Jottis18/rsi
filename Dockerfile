FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    MYSQL_HOST=mysql \
    MYSQL_USER=root \
    MYSQL_PASSWORD=rootpassword \
    MYSQL_DATABASE=testdb \
    USER_FLAG="SD{race_condition_refund_exploit_success}" \
    GUEST_FLAG="SD{guest_user_no_access}"

RUN apt-get update && apt-get install -y \
    build-essential \
    default-mysql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN echo "SD{root_flag_race_condition_2024}" > /seadragonsfinal

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir \
    waitress flask pymysql cryptography

EXPOSE 80

CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "app:app"]

