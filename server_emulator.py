#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask import render_template
import json

app = Flask(__name__)


@app.route("/")
def index():
    with open('parameters.json', 'r') as file:
        params_data = json.load(file)
    number_of_robots = params_data['number_of_robots']
    grid_length = params_data['grid_length']
    grid_width = params_data['grid_width']
    tasks = {"rows": grid_length, "cols": grid_width}
    return render_template('home.html', rows=grid_length, cols=grid_width, num=number_of_robots)


@app.route("/getPick/location=<location>")
def get_pick(location):
    pick_dump = open("./pick.json", 'r')
    data = json.load(pick_dump)
    # Status code 200
    if location in data.keys():
        response = {
            "error": False,
            "error_code": 0,
            "message": "Success",
            "pick": data[location]
        }

        return jsonify(response), 200
    # Status code 400
    elif location not in data.keys():
        response = {
            "error": True,
            "error_code": 1,
            "message": "Wrong Location provided",
        }

        return jsonify(response), 400
    else:
        response = {
            "error": True,
            "error_code": 2,
            "message": "Wrong Input",
        }

        return jsonify(response), 401


@app.route("/pickConfirm", methods=["POST"])
#Made some changes in confirm pick
def confirm_pick():
    pick_dump = open("./pick.json", 'r')
    data = json.load(pick_dump)
    confirm_data = request.get_json()
    if str(confirm_data["location"]) in data.keys():
        location = confirm_data["location"]
        for pick in data[str(location)]:
            if pick["check_digit"] == confirm_data["check_digit"] and pick["order_id"] == confirm_data["order_id"]:
                response = {
                    "error": False,
                    "error_code": 0,
                    "message": "Success",
                    "confirmed_qty": confirm_data["confirmed_qty"]
                }

                return jsonify(response), 200
        response = {
            "error": True,
            "error_code": 2,
            "message": "Wrong check_digit or order_id",
        }

        return jsonify(response), 401
        # Status code 400
    else:
        response = {
            "error": True,
            "error_code": 1,
            "message": "Wrong location",
        }
        
        return jsonify(response), 400


if __name__ == "__main__":
    app.run(debug=True)