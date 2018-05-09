FROM ***REMOVED***python-dev:3.6

COPY ./ /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/main.py"]
