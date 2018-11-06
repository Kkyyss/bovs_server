import json
import os
import time

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_restful import Resource, Api
from flask_mail import Mail, Message
from flask_cors import CORS

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    decode_token, get_jwt_identity
)


mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "bc.vote.newsletter@gmail.com",
    "MAIL_PASSWORD": "bcvote1234"
}

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.update(mail_settings)
app.config['JWT_SECRET_KEY'] = os.urandom(12)
cors = CORS(app)
jwt = JWTManager(app)
mail = Mail(app)
api = Api(app)


class EmailNotification(Resource):
    @jwt_required
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            emails = req['emails']
            print(emails)
            election = req['election']
            link = "http://localhost:3000/login/voter/"
            with mail.connect() as conn:
                print('inside mail connected')
                for email in emails:
                    token = create_access_token(identity={ 'email': email }, expires_delta=False)
                    link = link + email + "/" + token + "/" + req['addr']
                    msg = Message(
                        subject="[Blockchain Online Voting] Voting: " + election['title'] + " invitation",
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[email],
                        html="Hi User,<br/><br/><br/>" +
                        "You are invited to join an election: " + election['title'] + ".<br/>" +
                        "Please login to the <b>Blockchain Online Voting System</b>:<br/>" +
                        '<a  href="' + link + '" target="_blank">' + link + '</a><br/><br/><br/>' +
                        "Sent by Blockchain Online Voting System"
                    )
                    try:
                        mail.send(msg)
                    except:
                        return None, 400
                    return None, 200


class EmailSendToken(Resource):
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            if req['email'] and req['role']:
                token = create_access_token(identity={ 'email': req['email'] }, expires_delta=False)
                link = "http://localhost:3000/login/" + req['email'] + "/" + req['role'] + "/" + token
                with mail.connect() as conn:
                    msg = Message(
                        subject="[Blockchain Online Voting] Registration Verification",
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[req['email']],
                        html="Hi User,<br/><br/><br/>" +
                        "Before using the <b>Blockchain Online Voting System</b>, please verify your email address.<br/>" +
                        '<a  href="' + link + '" target="_blank">Verify Email</a><br/>' +
                        "Or verify using this link:<br/>" +
                        '<a  href="' + link + '" target="_blank">' + link + '</a><br/><br/><br/>' +
                        "Sent by Blockchain Online Voting System"
                    )
                    try:
                        mail.send(msg)
                    except:
                        return None, 400
                    return None, 200
                return None, 400
            return None, 400


class TokenVerification(Resource):

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()

        if not current_user:
            return None, 401

        return current_user, 200


class CurrentDateTime(Resource):
    def get(self):
        return jsonify({'now': int(time.time())})


api.add_resource(EmailNotification, '/email')
api.add_resource(EmailSendToken, '/token')
api.add_resource(TokenVerification, '/verification')
api.add_resource(CurrentDateTime, '/current-dt')

if __name__ == '__main__':
    app.run(debug=True)
