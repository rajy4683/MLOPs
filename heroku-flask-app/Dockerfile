FROM python:3.8.5-slim-buster AS compile-image
WORKDIR /app
#RUN adduser -D myuser
#USER myuser
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY './requirements.txt' .
RUN pip install -r requirements.txt

# COPY setup.py .
# RUN pip install .

FROM python:3.8.5-slim-buster AS build-image
COPY --from=compile-image /opt/venv /opt/venv
WORKDIR /app
COPY ./app .
RUN ls -lrt

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT  ["python", "app.py"]
CMD  ["-f", "static_cover.jpg"]
