import json
import bedrock_kb
import claude3_haiku_v1


def orchestrate(conversation_history, new_question):
    """Orchestrates RAG workflow based on conversation history
    and a new question. Returns an answer and a list of
    source documents."""

    # retrieve data from vector db based on question
    docs = bedrock_kb.get_relevant_docs(new_question, 6)

    # normalize source documents
    sources = bedrock_kb.format_sources(docs)

    # get model specific prompts
    system_prompt, user_prompt = claude3_haiku_v1.get_prompts()

    # build prompt based on new question and search results
    context = json.dumps(docs)
    prompt = user_prompt.format(context=context, question=new_question)

    # translate conversation history to messages
    messages = []
    for question in conversation_history["questions"]:
        messages.append(
            {"role": "user", "content": [{"text": question["q"]}]})
        messages.append(
            {"role": "assistant", "content": [{"text": question["a"]}]})

    # add new question message
    messages.append({"role": "user", "content": [{"text": prompt}]})

    # invoke LLM
    response = claude3_haiku_v1.generate_message(system_prompt, messages)

    return response, sources
