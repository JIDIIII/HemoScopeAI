# Local container notes

The API Dockerfile is services/api/Dockerfile. Build with:

~~~sh
docker build -f services/api/Dockerfile -t hemoscope-api:local services/api
docker run --rm -p 8000:8000 --env-file services/api/.env hemoscope-api:local
~~~

Do not include a production secrets file in an image. The current image contains no trained model and starts with inference unavailable.
