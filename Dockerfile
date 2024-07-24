FROM ai-chatbot.base:0.1.0
COPY . .
EXPOSE 8080
ENTRYPOINT ["python", "-u", "main.py"]
