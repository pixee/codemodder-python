import boto3
from flask import Flask, request

app = Flask(__name__)
AWS_SESSION = boto3.Session(
    aws_access_key_id="YOUR_ACCESS_KEY",
    aws_secret_access_key="YOUR_SECRET_KEY",
    region_name="YOUR_REGION",
)


@app.route("/login")
def login():
    dynamodb = AWS_SESSION.client("dynamodb")

    username = request.args["username"]
    password = request.args["password"]

    dynamodb.scan(
        FilterExpression="username = " + username + " and password = " + password,
        TableName="users",
        ProjectionExpression="username",
    )
