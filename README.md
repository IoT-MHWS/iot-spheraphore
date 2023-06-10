# IoT MHWS: Spheraphore
## Install
```
pip install poetry
poetry install
pre-commit install
```

### Docker Compose
And a template docker-compose file:
```yaml
services:
  app:
    # depends_on:
    #   - database
    build:
      context: .
      dockerfile: Dockerfile
    # image: 
    restart: always
    # command: ...
    # ports:
    #   - "8000:8000"
    # volumes:
    #   - ./<SOURCE>:/<WORKDIR>  # pass your files for quik-reload
    # environment:
    #   SECRET: local
```
