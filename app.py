from flask_cors import CORS
import os
import boto3
from flask import Flask, jsonify, request
from botocore.exceptions import ClientError
import logging

app = Flask(__name__)
CORS(app, origins="*")

# ✅ Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Config
REGION = os.environ.get("AWS_REGION", "ap-south-2")

# ✅ DynamoDB connection with retries
dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("Courses")

# ✅ Health check (ALB will use this)
@app.route("/vafiya-student/health")
def health():
    try:
        # simple DB check
        courses_table.table_status
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "error"}), 500


# ✅ Get single course
@app.route("/vafiya-student/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    try:
        resp = courses_table.get_item(Key={"code": course_code})
        item = resp.get("Item")

        if not item:
            return jsonify({"error": "Course not found"}), 404

        return jsonify(item), 200

    except Exception as e:
        logger.error(f"Error fetching course: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ✅ List courses
@app.route("/vafiya-student/courses", methods=["GET"])
def list_courses():
    try:
        resp = courses_table.scan(Limit=50)
        return jsonify(resp.get("Items", [])), 200

    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ✅ Add course
@app.route("/vafiya-student/courses", methods=["POST"])
def add_course():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        if "code" not in data or "name" not in data:
            return jsonify({"error": "Missing required fields: code, name"}), 400

        courses_table.put_item(
            Item=data,
            ConditionExpression="attribute_not_exists(code)"
        )

        return jsonify({"message": "Course added successfully"}), 201

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"error": "Course already exists"}), 409

        logger.error(f"DynamoDB error: {str(e)}")
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ❗ IMPORTANT: Use production server in container
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)