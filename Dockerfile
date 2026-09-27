FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default for local `docker run`. Render overrides this with its own
# PORT value at runtime, and the shell-form CMD below expands it -
# never hardcode the bind port, or Render's proxy can't reach the app.
ENV PORT=5000
EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:$PORT app:app
