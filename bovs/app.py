import json
import os
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_restful import Resource, Api
from flask_mail import Mail, Message
from flask_cors import CORS

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    decode_token, get_jwt_identity
)

scheduler = BackgroundScheduler()
scheduler.start()

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "bc.vote.newsletter@gmail.com",
    "MAIL_PASSWORD": "bcvote1234"
}

app = Flask(__name__, static_folder='static', static_url_path='', template_folder='template')
app.config.update(mail_settings)
app.config['JWT_SECRET_KEY'] = os.urandom(12)
cors = CORS(app)
jwt = JWTManager(app)
mail = Mail(app)
api = Api(app)


def sendEventStatusNotification(data):
    with app.app_context():
        emails = data['emails']
        addr = data['addr']
        election = data['election']
        isStart = data['start']
        creator = data['creator']
        r_link = "http://localhost:3000/login/"
        token = create_access_token(identity={ 'email': creator }, expires_delta=False)
        link = r_link + 'organizer/' + creator + "/" + token + "/" + addr
        content= "The poll " + election['title'] + " was" + (" begin" if isStart else " over") + "." + \
            " Please access the link to " + ("vote" if isStart else "view results") + ":"
        msg = Message(
            subject="[BOVS - Blockchain Online Voting System] Voting: " + election['title'] + (" started" if isStart else " closed"),
            sender=app.config.get("MAIL_USERNAME"),
            recipients=[creator],
            html=render_template("email_template.html", content=content, link=link)
        )
        try:
            mail.send(msg)
        except Exception as e:
            return e.message, 400
        for email in emails:
            if email == creator:
                continue
            token = create_access_token(identity={ 'email': email }, expires_delta=False)
            link = r_link + 'voter/' + email + "/" + token + "/" + addr
            content = "The poll " + election['title'] + " was" + (" begin" if isStart else " over") + "." + \
                " Please access the link to " + ("vote" if isStart else "view results") + ":"
            msg = Message(
                subject="[BOVS - Blockchain Online Voting System] Voting: " + election['title'] + (" started" if isStart else " closed"),
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[email],
                html=render_template("email_template.html", content=content, link=link)
            )
            try:
                mail.send(msg)
            except Exception as e:
                return e.message, 400

        return None, 200


class CloseEmailNotification(Resource):
    @jwt_required
    def post(self):
        if request.data:
            req = request.get_json(force=True)
            emails = req['emails']
            title = req['title']
            creator = req['creator']
            addr = req['addr']
            r_link = "http://localhost:3000/login/"
            token = create_access_token(identity={ 'email': creator }, expires_delta=False)
            link = r_link + 'organizer/' + creator + "/" + token + "/" + addr
            content =  "The poll " + title + " was over." + \
                " Please access the link to view results."
            msg = Message(
                subject="[BOVS - Blockchain Online Voting System] Voting: " + title + " closed",
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[creator],
                html=render_template("email_template.html", content=content, link=link)
            )
            try:
                mail.send(msg)
            except Exception as e:
                return e.message, 400

            for email in emails:
                if email == creator:
                    continue
                token = create_access_token(identity={ 'email': email }, expires_delta=False)
                link = r_link + 'voter/' + email + "/" + token + "/" + addr
                content =  "The poll " + title + " was over." + \
                        " Please access the link to view results."
                msg = Message(
                    subject="[BOVS - Blockchain Online Voting System] Voting: " + title + " closed",
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[email],
                    html=render_template("email_template.html", content=content, link=link)
                )
                try:
                    mail.send(msg)
                except Exception as e:
                    return e.message, 400

            return None, 200


# To notify the users the status of the poll (i.e. instant notification, scheduled notification)
class EmailNotification(Resource):
    @jwt_required                                       # JWT verification
    def post(self):
        if request.data:
            req = request.get_json(force=True)          # retrieve the data from API request by the client side
            emails = req['emails']                      # get voters' email
            startDate = req['startDate']                # get start date
            isManual = req['isManual']                  # get end date mode
            endDate = req['endDate']                    # get end date
            election = req['election']                  # get election data
            r_link = "http://localhost:3000/login/"     # root URL
            # Send all the emails with a loop
            for email in emails:
                token = create_access_token(identity={ 'email': email }, expires_delta=False)
                link = r_link + 'voter/' + email + "/" + token + "/" + req['addr']
                content = "You are invited to join a poll: " + election['title'] + "." + \
                    " Please access the link to participate."
                msg = Message(
                    subject="[BOVS - Blockchain Online Voting System] Voting: " + election['title'] + " invitation",
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[email],
                    html=render_template("email_template.html", content=content, link=link)
                )
                try:
                    mail.send(msg)
                except Exception as e:
                    return e.message, 400

            # Start date mode: Custom
            if election['startNow'] == False:
                # Schedule the start poll notification
                scheduler.add_job(sendEventStatusNotification, 'date', run_date=startDate,
                                  args=[{ 'emails': emails, 'creator': req['creator'], 'election': election, 'addr': req['addr'], 'start': True }])
            # End date mode: Custom
            if isManual == False:
                # Schedule the end poll notification
                scheduler.add_job(sendEventStatusNotification, 'date', run_date=endDate,
                                  args=[{ 'emails': emails, 'creator': req['creator'], 'election': election, 'addr': req['addr'], 'start': False }])
            return None, 200


# send magic link and JWT token
class EmailSendToken(Resource):
    def post(self):
        if request.data:
            req = request.get_json(force=True) # retrieve the data from API request by the client side
            if req['email'] and req['role']:
                # create JWT token
                token = create_access_token(identity={ 'email': req['email'] }, expires_delta=False)
                link = "http://localhost:3000/login/basic/" + req['email'] + "/" + req['role'] + "/" + token
                content = "Please access the link to login."

                msg = Message(
                    subject="[BOVS - Blockchain Online Voting System] Login Verification",
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[req['email']],
                    html=render_template("email_template.html", content=content, link=link)
                )
                try:
                    mail.send(msg)
                except Exception as e:
                    return e.message, 400

                return None, 200

            return None, 400


# magic link token verification
class TokenVerification(Resource):
    @jwt_required
    def get(self):
        # verify the user
        current_user = get_jwt_identity()

        if not current_user:
            return None, 401

        return current_user, 200


# Get the current date adn time of the server
class CurrentDateTime(Resource):
    def get(self):
        return jsonify({'now': int(time.time())})


api.add_resource(EmailNotification, '/email')
api.add_resource(CloseEmailNotification, '/close-email')
api.add_resource(EmailSendToken, '/token')
api.add_resource(TokenVerification, '/verification')
api.add_resource(CurrentDateTime, '/current-dt')

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)
