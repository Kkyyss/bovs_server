import json
import os

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_mail import Mail, Message
from flask_cors import CORS

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    decode_token
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
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            emails = req['emails']
            election = req['election']
            link = "http://localhost:3000/"
            with mail.connect() as conn:
                for email in emails:
                    msg = Message(
                        subject="[Blockchain Online Voting] You are invited to join an election: " + election['title'],
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
                        return None


class EmailSendToken(Resource):
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            if req['email']:
                token = create_access_token(identity=req['email'], expires_delta=False)
                link = "http://localhost:3000/register/" + token
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
                        return None


class TokenVerification(Resource):
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            if req['token']:
                try:
                    data = decode_token(req['token']);
                except:
                    return None

                return data["identity"]
        return None


api.add_resource(EmailNotification, '/email')
api.add_resource(EmailSendToken, '/token')
api.add_resource(TokenVerification, '/verification')

if __name__ == '__main__':
    app.run(debug=True)
