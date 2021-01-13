# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
#eNV WEBSITES_ENABLE_APP_SERVICE_STORAGE=true

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
WORKDIR /app

VOLUME /app/contable/database

# Install pip requirements
# install FreeTDS and dependencies

ADD . /app
ADD contable/requirements.txt .
RUN python -m pip install -r requirements.txt
RUN cp -r venv/lib/python3.6/site-packages/adminlte3/  /usr/local/lib/python3.8/site-packages
RUN cp -r venv/lib/python3.6/site-packages/adminlte3_theme/ /usr/local/lib/python3.8/site-packages
WORKDIR /app/contable
#RUN python manage.py collectstatic --noinput

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
#RUN useradd appuser && chown -R appuser /app
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# File wsgi.py was not found in subfolder: 'Habitat'. Please enter the Python path to wsgi file.

CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]
#RUN python manage.py runserver 0.0.0.0:8000
