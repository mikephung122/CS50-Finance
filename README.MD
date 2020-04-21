# CS50 Finance
This is the final project for CS50's Introduction to Computer Science - An introduction to the intellectual enterprises of computer science and the art of programming.  In this project, we were tasked with implementing a fully functional website for users to "buy" and "sell" stocks in a practice environment.

https://docs.cs50.net/2019/x/psets/8/finance/finance.html#distribution

## Overview
Static - Contains CSS styling and any other static resources.
Templates - HTML templates with Jinja Templating.
application.py - Flask Application and app routes.
finance.db - sqlite Database for logging transactions and users.
helpers.py - Utility functions used by the APIs.

## Setup
- Clone the repository
- Install the requirements
- export FLASK_APP={directory/application.py}
- export API_KEY={IEX API Key - https://iexcloud.io/}
- flask run
