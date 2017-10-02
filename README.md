# Install Instructions
Install libraries

Make sure pipenv is installed
`pip install pipenv`

Install packages using pipenv
`pipenv install`

Create database. From MySQL CLI
`create database weather;`

from project root, Install app after entering the environment
`pipenv shell; pip install --editable .`

# Run App Instructions
Activate your environment
`pipenv shell`

Set FLASK_APP env
`export FLASK_APP='run_app:app`

Initialize Database
`flask initdb`

Load included sqltables into MySQL. If you get file not found, make sure you are running from the project root
`flask loaddb`

Run Flask
`flask run`

# Database reasoning
Instead of using the csv directly as a large object, I've done a bit of normalization.
This helps eliminate deletion anomalies. For example, if the latitude of a station ever changes, if we used the csv format, there is a chance we forget to edit a row, resulting in an inconsistent data. Instead, I norrmalize so the station data is extracted into its own table
and the timeseries data is placed into its own table

One more notable decision is to use an autoincrement id instead of the station id. The reason for this is two fold. First, we save a bit of space in indexes and table space. Instead of storing the varchar that is the station id, we store the integer ID. Secondly, we have little control over the station id. It is possible the weather service decides one day that the station ids will change their format altogether. This would lead to a pretty painful migration

# API Usage
The api is
`/api/city/<cityname>?unit=[F,C]`
You can reach it at localhost:5000 after you have flask running
The response will look like the example.json file in the repo

# Run Tests
After install, run py.test on the tests directory
`py.test tests`
