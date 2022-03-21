FROM tclarke104/med-ai-runner:0.1

CMD python -m celery -A runner worker  -E -Q celery -c 1 