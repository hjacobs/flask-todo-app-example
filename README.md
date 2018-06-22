# flask-todo-app-example

```
pipenv install --dev
pipenv shell
docker run -d --name todo-app-redis -p 6379:6379 redis:4-alpine
GITHUB_CLIENT_ID=c1cd07b88231aaf552e4 GITHUB_CLIENT_SECRET=54cfdc69330e47e0e4ddeb9f10e26d919d590e3e OAUTHLIB_INSECURE_TRANSPORT=1 SECRET_KEY=local ./app.py
```

```
docker build -t todo-app .
docker run -it -p 8080:8080 todo-app
```
