# translation-service-challenge

> A simple translation service.

- [Development](#development)
- [Running in production](#running-in-production)
- [Running with Docker](#running-with-docker)

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
