FROM tclarke104/med-ai-runner:0.1

CMD python -m celery -A runner beat 