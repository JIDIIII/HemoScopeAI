# Local container notes

The API Dockerfile is services/api/Dockerfile. Build with:

~~~sh
docker build -f services/api/Dockerfile -t hemoscope-api:local services/api
docker run --rm -p 8000:8080 --env-file services/api/.env hemoscope-api:local
~~~

The container reads the runtime port from `PORT` (8080 by default), so the same image works on managed container hosts. The example maps it to port 8000 on the development computer. Do not include a production secrets file in an image. The current image contains no trained model and starts with inference unavailable.

See [zero-dollar hosting options](../hosting/README.md) for the Render Free and OCI Always Free deployment profiles and future Huawei path.
