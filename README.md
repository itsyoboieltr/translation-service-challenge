# translation-service-challenge

> A simple translation service.

- [Development](#development)
- [Running in production](#running-in-production)
- [Running with Docker](#running-with-docker)
- [Environment variables](#environment-variables-env)

This project uses [Rye](https://rye-up.com/) as a comprehensive project and package management solution. Instructions on how to install `Rye` can be found [here](https://rye-up.com/guide/installation/).

## Development:

1. `rye sync`: install dependencies

2. `rye run dev`: start the server with hot-reloading

## Running in production:

1. `rye sync`: install dependencies

2. `rye run start`: start the server

## Running with Docker:

1. `docker compose up -d`: start the app with a MongoDB instance.

2. `docker compose down`: stop all processes.

## Environment variables ([.env](.env.example)):

- `DATABASE_URL`: database connection URL for MongoDB. This is required by the app to function, otherwise it will crash immediately on startup.

- `MONGO_INITDB_ROOT_USERNAME`: MongoDB root username used by Docker Compose. Default: `root`

- `MONGO_INITDB_ROOT_PASSWORD`: MongoDB root password used by Docker Compose. Default: `example`
