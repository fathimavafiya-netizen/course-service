from flask_cors import CORS
import os
import boto3
from flask import Flask, jsonify, request
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app, origins="*")


REGION = os.environ.get("AWS_REGION", "ap-south-2")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("Courses")


@app.route("/vafiya-student/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/vafiya-student/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    resp = courses_table.get_item(Key={"code": course_code})
    item = resp.get("Item")
    if not item:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(item), 200


@app.route("/vafiya-student/courses", methods=["GET"])
def list_courses():
    resp = courses_table.scan(Limit=50)
    return jsonify(resp.get("Items", [])), 200


@app.route("/vafiya-student/courses", methods=["POST"])
def add_course():
    try:
        data = request.get_json()

        if not data or "code" not in data or "name" not in data:
            return jsonify({"error": "Missing required fields: code, name"}), 400

        courses_table.put_item(
            Item=data,
            ConditionExpression="attribute_not_exists(code)"
        )

        return jsonify({"message": "Course added successfully"}), 201

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"error": "Course already exists"}), 409
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)