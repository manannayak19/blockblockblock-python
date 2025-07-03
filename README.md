# blockblockblock-python
A simple blockchain implementation in Python with a basic REST API using Flask.

# Simple Python Blockchain

It includes a proof-of-work system, transaction management, and a REST API using Flask.

## Features

- Create and store blocks in a chain
- Add and broadcast transactions
- Simple Proof of Work algorithm
- Basic consensus mechanism to resolve conflicts across nodes
- RESTful API to interact with the blockchain

---

## Technologies Used

- Python 3
- Flask

---

## API Endpoints

| Method | Endpoint              | Description                        |
|--------|-----------------------|------------------------------------|
| GET    | `/mine`               | Mines a new block                  |
| POST   | `/transactions/new`   | Adds a new transaction             |
| GET    | `/chain`              | Returns the full blockchain        |
| POST   | `/nodes/register`     | Register new nodes to the network  |
| GET    | `/nodes/resolve`      | Reaches consensus between nodes    |

---
Blockchain tutorial - https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

