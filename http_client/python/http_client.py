import json
import logging
import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

SECRET_AUTH_TOKEN = "abcdefghijklmopqrstuvxyz123456789"  # This token must match the sender's configuration

last_received_data_time = 0
RECEIVER_HEARTBEAT_TIMEOUT_SECONDS = 15.0


@app.route("/", methods=["POST"])
def receive_gsi_data():
    global last_received_data_time

    if not request.is_json:
        app.logger.warning("Received non-JSON request from %s", request.remote_addr)
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()

    received_token = data.get("auth", {}).get("token")
    if received_token != SECRET_AUTH_TOKEN:
        app.logger.error(
            f"Unauthorized access attempt from {request.remote_addr}! Received token: {received_token}"
        )
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    last_received_data_time = time.time()

    try:
        provider_name = data.get("provider", {}).get("name", "N/A")
        player_name = data.get("player", {}).get("name", "N/A")
        player_health = data.get("player", {}).get("health", "N/A")
        map_name = data.get("map", {}).get("name", "N/A")
        round_phase = data.get("map", {}).get("round", {}).get("phase", "N/A")
        game_phase = data.get("map", {}).get("phase", "N/A")

        app.logger.info(f"--- GSI Data Received (from {request.remote_addr}) ---")
        app.logger.info(f"  Source Game: {provider_name}")
        app.logger.info(f"  Player: {player_name} | Health: {player_health}")
        app.logger.info(
            f"  Map: {map_name} | Round Phase: {round_phase} | Game Phase: {game_phase}"
        )

        if "previously" in data:
            app.logger.info(
                f"  Previously changed data: {json.dumps(data['previously'], indent=2)}"
            )
        if "added" in data:
            app.logger.info(
                f"  Newly added data: {json.dumps(data['added'], indent=2)}"
            )

        return jsonify(
            {"status": "success", "message": "GSI data received and processed"}
        ), 200

    except Exception as e:
        app.logger.exception(
            f"Error processing GSI data from {request.remote_addr}: {e}"
        )
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500


def receiver_heartbeat_monitor():
    app.logger.info(
        f"Receiver Heartbeat Monitor started. Expecting data every ~{RECEIVER_HEARTBEAT_TIMEOUT_SECONDS}s."
    )
    is_sender_connected = False

    while True:
        time.sleep(1)

        if last_received_data_time == 0:
            if is_sender_connected:
                app.logger.info(
                    "Awaiting first GSI data from sender or re-connection..."
                )
                is_sender_connected = False
            continue

        time_since_last_received = time.time() - last_received_data_time

        if time_since_last_received > RECEIVER_HEARTBEAT_TIMEOUT_SECONDS:
            if is_sender_connected:
                app.logger.error(
                    f"GSI SENDER DISCONNECTED! No data received for {time_since_last_received:.1f} seconds."
                )
                is_sender_connected = False
        else:
            if not is_sender_connected:
                app.logger.info(
                    f"GSI SENDER CONNECTED! Data received after {time_since_last_received:.1f} seconds."
                )
                is_sender_connected = True


if __name__ == "__main__":
    monitor_thread = threading.Thread(target=receiver_heartbeat_monitor, daemon=True)
    monitor_thread.start()

    app.logger.info("GSI Receiver (Flask) starting on http://127.0.0.1:5000/")
    app.logger.info(
        f"Expected Auth Token: '{SECRET_AUTH_TOKEN}' (must match sender's config)"
    )

    app.run(host="127.0.0.1", port=5000, debug=True)  # , ssl_context="adhoc")
