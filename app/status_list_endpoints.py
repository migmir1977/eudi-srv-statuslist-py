# coding: latin-1
###############################################################################
# Copyright (c) 2023 European Commission
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
from urllib.parse import unquote, urlparse
from flask import Blueprint, current_app, jsonify, request, send_from_directory

from app.list_management import (
    dump_list,
    generate_StatusListInfo,
    load_list,
    status_list,
    new_list,
    take_index_list,
)

token = Blueprint("token_status_list", __name__, url_prefix="/token_status_list")
from app.config_service import ConfService as cfgservice


@token.route("/take", methods=["POST"])
def take_index():

    #cfgservice.app_logger.info("Take Request, header: " + str(request.headers) + ", payload: " + str(request.form.to_dict()))

    api_key = request.headers.get("X-Api-Key")
    print("API_Key recieved: ", api_key, flush=True)
    print("API_Key from env: ", current_app.config['API_key'], flush=True)
    if api_key != current_app.config['API_key']:
        return jsonify({"message": "Unauthorized access"}), 401

    doctype = request.form["doctype"]
    #external_doctype = request.form.get("doctype", "").strip()    
    #ALLOWED_DOCTYPES = {"json"}
    #if external_doctype not in ALLOWED_DOCTYPES:
    #    abort(400, "Invalid doctype")    
    #else
    #    doctype="json"
        
    country = request.form["country"]
    expiry_date = request.form["expiry_date"]

    if country not in status_list:
        new_list(country,doctype)
    #if doctype not in status_list:
    #    new_list(doctype)
    status_info = generate_StatusListInfo(country,doctype,expiry_date)
    
    print("\nStatus Info: ", status_info, flush=True)

    return jsonify(status_info)


@token.route("/get", methods=["GET"])
def get_index():

    print("\nargs: ", request.args, flush=True)

    """ api_key = request.headers.get("X-Api-Key")
    if api_key != current_app.config['API_key']:
        return jsonify({"message": "Unauthorized access"}), 401 """


    uri = request.args.get("uri")
    
    index = request.args.get("id") or request.args.get("idx")

    if uri is None or index is None:
        return jsonify({"error": "Missing URI or idx/id"}), 400
    
    try:
        index = int(index)
    except ValueError:
        return jsonify({"error": "'id' or 'idx' unkown"}), 400

    uri = unquote(uri)
    temp_list = load_list(uri)

    if "token_status_list" in uri:
        return str(temp_list["token_status_list"].status_list.get(index))
    elif "identifier_list" in uri:
        if str(index) not in temp_list["identifier_list"]:
            return str(0)
        else:
            return str(temp_list["identifier_list"][str(index)])
    else:
        return jsonify({"error": "Missing URI or index"}), 400


@token.route("/set", methods=["POST"])
def set_index():
    api_key = request.headers.get("X-Api-Key")
    if api_key != current_app.config['API_key']:
        return jsonify({"message": "Unauthorized access"}), 401

    uri = request.form["uri"]

    index = request.form.get("id") or request.form.get("idx")
    
    status = request.form["status"]

    if uri is None or index is None or status is None:
        return jsonify({"error": "Missing URI/index/status"}), 400

    
    try:
        index = int(index)
    except ValueError:
        return jsonify({"error": "'id' or 'idx' unkown"}), 400

    try:
        status = int(status)
    except ValueError:
        return jsonify({"error": " status unkown"}), 400

    if status != 1:
        return jsonify({"error": "Wrong Status Change"}), 400

    temp_list = load_list(uri)
    
    temp_list["token_status_list"].status_list.set(index, status)

    temp_list["identifier_list"].update({str(index): status})

    parsed_url = urlparse(uri)
    path_parts = parsed_url.path.split("/")
    country = path_parts[2]
    doctype = path_parts[3]

    dump_list(temp_list, country, doctype)

    return "Status Changed\n"


@token.route("/static/swagger.json")
def swagger_static():
    return send_from_directory("static", "swagger.json")
