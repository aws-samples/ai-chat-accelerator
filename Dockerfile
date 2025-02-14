FROM ai-chatbot.base:0.1.0
RUN mkdir -p /app/tmp && chmod 777 /app/tmp
ENV TMPDIR=/app/tmp
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
COPY . .
EXPOSE 8080
ENTRYPOINT ["gunicorn", \
            "--bind", "0.0.0.0:8080", \
            "--workers", "1", \
            "--threads", "4", \
            "--worker-class", "gthread", \
            "main:app"]
