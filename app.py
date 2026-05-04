import os
import boto3
from flask import Flask, jsonify
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = Flask(__name__)

# X-Ray config
xray_recorder.configure(service="course-service")
XRayMiddleware(app, xray_recorder)

# AWS config
REGION = os.environ.get("AWS_REGION", "ap-south-2")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("Courses")

# ✅ ROOT ROUTE (VERY IMPORTANT)
@app.route("/")
def home():
    return jsonify({
        "message": "Course Service Running",
        "endpoints": [
            "/health",
            "/courses",
            "/courses/<course_code>"
        ]
    }), 200

# ✅ HEALTH CHECK (for ALB)
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "course-service"}), 200

# Get single course
@app.route("/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    resp = courses_table.get_item(Key={"code": course_code})
    item = resp.get("Item")
    if not item:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(item), 200

# List courses
@app.route("/courses", methods=["GET"])
def list_courses():
    resp = courses_table.scan(Limit=50)
    return jsonify(resp.get("Items", [])), 200

# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)