import logging
import log
import sys
import signal
from datetime import datetime, timezone
from flask import Flask, request, render_template, abort
from markupsafe import Markup
import markdown
import database
import orchestrator


def signal_handler(signal, frame):
    logging.warning('SIGTERM received, exiting...')
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
app = Flask(__name__)


@app.before_request
def before_request():
    """log http request (except for health checks)"""
    if request.path != "/health":
        logging.info(f"HTTP {request.method} {request.url}")


@app.after_request
def after_request(response):
    """log http response (except for health checks)"""
    if request.path != "/health":
        logging.info(
            f"HTTP {request.method} {request.url} {response.status_code}")
    return response


# initialize database client
db = database.Database()


@app.template_filter('markdown')
def render_markdown(text):
    """Render Markdown text to HTML"""
    return Markup(markdown.markdown(text))


@app.route("/health")
def health_check():
    return "healthy"


def get_current_user_id():
    """get the currently logged in user"""
    # TODO: get current user id from auth
    return "1"


def get_chat_history(user_id):
    """
    fetches the user's latest chat history
    """
    logging.info(f"fetching chat history for user {user_id}")

    # fetch last 10 questions from db
    history = db.list_by_user(user_id, 10)

    # build list of objects that have
    # the first question in each conversation and the date
    result = []
    for h in history:
        if len(h["questions"]) == 0:
            continue
        result.append({
            "conversationId": h["conversationId"],
            "created": datetime.fromisoformat(h["created"]).strftime("%B %d, %Y"),
            "initial_question": h["questions"][0]["q"],
        })
    return result


@app.route("/")
def index():
    """home page"""
    user_id = get_current_user_id()
    return render_template("index.html",
                           conversation={},
                           chat_history=get_chat_history(user_id))


@app.route("/new", methods=["POST"])
def new():
    """POST /new starts a new conversation"""
    return render_template("chat.html", conversation={})


@app.route("/ask", methods=["POST"])
def ask():
    """POST /ask adds a new Q&A to the conversation"""

    # get conversation id and question from form
    if "conversation_id" not in request.values:
        m = "missing required form data: conversation_id"
        logging.error(m)
        abort(400, m)
    id = request.values["conversation_id"]
    logging.info(f"conversation id: {id}")

    if "question" not in request.values:
        m = "missing required form data: question"
        logging.error(m)
        abort(400, m)
    question = request.values["question"]
    question = question.rstrip()
    logging.info(f"question: {question}")

    user_id = get_current_user_id()

    # if conversation id is blank, start a new one
    # else, fetch conversation history from db
    if id == "":
        conversation = db.new(user_id, datetime.now(timezone.utc).isoformat())
    else:
        conversation = db.get(id)
        logging.info("fetched conversation")
        log.debug(conversation)

    _, conversation, sources = ask_internal(conversation, question)

    # render ui with question history, answer, and top 3 document references
    return render_template("body.html",
                           conversation=conversation,
                           sources=sources,
                           chat_history=get_chat_history(user_id))


@app.route("/conversation/<id>", methods=["GET"])
def get_conversation(id):
    """GET /conversation/<id> fetches a conversation by id"""

    conversation = db.get(id)
    return render_template("chat.html", conversation=conversation)


@app.route("/api/ask", methods=["POST"])
def ask_api_new():
    """returns an answer to a question in a new conversation"""

    # get request json from body
    body = request.get_json()
    log.debug(body)
    if "question" not in body:
        m = "missing field: question"
        logging.error(m)
        abort(400, m)
    question = body["question"]

    conversation = db.new(datetime.now(timezone.utc))

    answer, conversation, sources = ask_internal(conversation, question)

    return {
        "conversationId": conversation["conversationId"],
        "answer": answer,
        "sources": sources,
    }


@app.route("/api/ask/<id>", methods=["POST"])
def ask_api(id):
    """returns an answer to a question in a conversation"""

    # get request json from body
    body = request.get_json()
    log.debug(body)
    if "question" not in body:
        m = "missing field: question"
        logging.error(m)
        abort(400, m)
    question = body["question"]

    if id == "":
        m = "conversation id is required"
        logging.error(m)
        abort(400, m)
    else:
        conversation = db.get(id)
        logging.info("fetched conversation")
        log.debug(conversation)

    answer, _, sources = ask_internal(conversation, question)

    return {
        "conversationId": id,
        "answer": answer,
        "sources": sources,
    }


@app.route("/api/conversations")
def conversations_list():
    """fetch top 10 conversations"""
    return db.list(10)


@app.route("/api/conversations/users/<user_id>")
def conversations_get_by_user(user_id):
    """fetch top 10 conversations for a user"""
    return db.list_by_user(user_id, 10)


@app.route("/api/conversations/<id>")
def conversations_get(id):
    """fetch a conversation by id"""
    return db.get(id)


def ask_internal(conversation, question):
    """
    core ask implementation shared by app and api.

    Args:
        conversation: conversation object
        question: question to ask

    Returns:
        answer: answer to question
        conversation: updated conversation object
        sources: search results
    """

    # RAG orchestration to get answer
    answer, sources = orchestrator.orchestrate(conversation, question)

    # add final Q&A to conversation
    conversation["questions"].append({
        "q": question,
        "a": answer,
        "created": datetime.now(timezone.utc),
    })

    logging.info("updating conversation in db")
    log.debug(conversation)
    db.update(conversation)

    return answer, conversation, sources


if __name__ == '__main__':
    port = 8080
    print(f"listening on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
