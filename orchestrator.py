import json
import bedrock_kb
import claude3_haiku_v1


def orchestrate(conversation_history, new_question):
    """Orchestrates RAG workflow based on conversation history
    and a new question. Returns an answer and a list of
    source documents."""

    # get model specific prompts
    system_prompt, user_prompt, reword_prompt = claude3_haiku_v1.get_prompts()
    query = new_question

    # for follow up questions, use llm to re-word with context from
    # previous questions in the conversation
    if len(conversation_history["questions"]) > 0:
        past_q = [question["q"]
                  for question in conversation_history["questions"]]
        p = reword_prompt.format(
            past_questions=json.dumps(past_q, indent=2),
            new_question=new_question,
        )
        messages = [{"role": "user", "content": [{"text": p}]}]
        query = claude3_haiku_v1.generate_message(messages)

    # retrieve data from vector db based on question
    docs = bedrock_kb.get_relevant_docs(query, 6)

    # normalize source documents
    sources = bedrock_kb.format_sources(docs)

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
    response = claude3_haiku_v1.generate_message(
        messages, system_prompt=system_prompt)

    return response, sources
