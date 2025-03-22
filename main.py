from flask import Flask, jsonify, request, abort
import os
import uuid
from Global.EncoderOptions import *
from StreamManager import *
import sqlite3
import shutil

# Create Flask app
app = Flask(__name__)

# Initialize the VideoStreamManager
stream_manager = StreamManager()

# Directory containing media files
MEDIA_FOLDER = ".\\media"
OUTPUT_FOLDER = ".\\tmp"
DATABASE = "sessions.db"


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                instance_id TEXT PRIMARY KEY,
                active BOOLEAN NOT NULL,
                group_id TEXT
            )
        ''')
        conn.commit()

init_db()
    

# Endpoint 1: Get a list of all media files in the folder
@app.route("/media-files", methods=["GET"])
def get_media_files():
    try:
        # List all files in the media folder
        files = [file for file in os.listdir(MEDIA_FOLDER) if os.path.isfile(os.path.join(MEDIA_FOLDER, file))]
        return jsonify({"media_files": files})
    except Exception as e:
        return jsonify({"error": f"Error reading media folder: {str(e)}"}), 500


# Endpoint 2: Start encoding
@app.route("/start-encoding", methods=["POST"])
def start_encoding():
    data = request.get_json()

    if not data or "file_name" not in data:
        abort(400, description="Request must contain 'file_name'.")
    
    if not data or "instance" not in data:
        abort(400, description="Request must contain 'instance'")

    file_name = data["file_name"]
    instance_id = data["instance"]
    input_file = os.path.join(MEDIA_FOLDER, file_name)
    input_file = f"{MEDIA_FOLDER}\{file_name}"
    output_temp = file_name.split('.')[0]
    output_file = os.path.join(OUTPUT_FOLDER, output_temp )
    

    # Check if the file exists
    if not os.path.isfile(input_file):
        abort(404, description=f"File '{file_name}' not found in the media folder.")

    # Generate a unique instance ID
    #instance_id = str(uuid.uuid4())
    output_folder = f"{OUTPUT_FOLDER}\{instance_id}"
    os.makedirs(output_folder, exist_ok=True)
    output_file = f"{OUTPUT_FOLDER}\{instance_id}\{output_temp}"
    output_file_name = output_file + "_playlist.m3u8"  # Output playlist file name
    output_file = output_file_name

    # Configure default options
    video_options = VideoOptions()
    audio_options = AudioOptions()
    mapping_options = MappingOptions()
    hls_options = HLSOptions(segment_filename="segment_%03d.ts")

    try:
        # Start the encoding process
        stream_manager.start_video_stream(
            instance_id, input_file, output_file, video_options, audio_options, mapping_options, hls_options
        )
        return jsonify({"instance": instance_id, "output_playlist": output_file_name})
    except Exception as e:
        return jsonify({"error": f"Error starting encoding: {str(e)}"}), 500

# Endpoint 3: Cancel encoding by instance ID
@app.route("/cancel-encoding/<instance_id>", methods=["POST"])
def cancel_encoding(instance_id):
    try:
        stream_manager.cancel_video_stream(instance_id)
        return jsonify({"status": "success", "message": f"Instance '{instance_id}' cancelled."})
    except ValueError as e:
        abort(404, description=str(e))
    except Exception as e:
        return jsonify({"error": f"Error cancelling encoding: {str(e)}"}), 500

@app.route("/start-instance", methods=["POST"])
def start_instance():
    """
    Start a new session, return instance_id, and update the database.
    """
    try:
        # Generate a unique instance_id
        instance_id = str(uuid.uuid4())

        # Extract group_id from the request (optional, can be null)
        data = request.get_json()
        group_id = data.get("group_id", None)

        # Update the SQLite database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (instance_id, active, group_id)
                VALUES (?, ?, ?)
            ''', (instance_id, True, group_id))
            conn.commit()

        # Return the instance_id
        return jsonify({"instance_id": instance_id}), 201

    except Exception as e:
        return jsonify({"error": f"Error starting instance: {str(e)}"}), 500


# Endpoint 2: Close an instance (session)
@app.route("/close-instance/<instance_id>", methods=["POST"])
def close_instance(instance_id):
    """
    Close the session, update the database, and clean up the temp folder.
    """
    try:
        # Check if the instance exists
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT group_id, active FROM sessions WHERE instance_id = ?', (instance_id,))
            row = cursor.fetchone()

        if not row:
            abort(404, description=f"Instance '{instance_id}' not found.")

        group_id, active = row

        # Update or delete the record based on the group_id
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            if group_id is None:
                # Delete the record if group_id is null
                cursor.execute('DELETE FROM sessions WHERE instance_id = ?', (instance_id,))
            else:
                # Update the active status to False
                cursor.execute('UPDATE sessions SET active = ? WHERE instance_id = ?', (False, instance_id))
            conn.commit()

        # Remove the subfolder inside temp
        temp_subfolder = os.path.join(OUTPUT_FOLDER, instance_id)
        if os.path.exists(temp_subfolder):
            shutil.rmtree(temp_subfolder)

        return jsonify({"status": "success", "message": f"Instance '{instance_id}' closed."})

    except Exception as e:
        return jsonify({"error": f"Error closing instance: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
