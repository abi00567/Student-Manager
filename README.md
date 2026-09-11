# Student Record Manager

A simple CRUD web application built using Flask and PostgreSQL.

## Technologies

- Python
- Flask
- PostgreSQL
- Docker
- Docker Compose
- HTML
- CSS
- JavaScript
- GitHub Actions
- Ansible

## Architecture

Browser
   |
   v
Flask Web Application
   |
   v
PostgreSQL Database

Both services run using Docker Compose.

## How to Run

1. Make sure Docker Desktop is running.

2. Open terminal inside the project folder.

3. Run:

docker compose up --build

4. Open the browser:

http://localhost:5000

## Features

- Add student
- View students
- Edit student
- Delete student

## Stop the Application

Press:

Ctrl + C

Or run:

docker compose down

## Database

PostgreSQL data is stored using a Docker named volume.

## CI/CD

GitHub Actions builds the Docker Compose services whenever code is pushed.