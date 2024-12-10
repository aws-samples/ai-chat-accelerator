import logging
import log
import boto3

model_id = "anthropic.claude-3-haiku-20240307-v1:0"
bedrock = boto3.client("bedrock-runtime")

system_prompt = ""
with open("prompts/claude3/haiku-v1/system.md", "r") as f:
    system_prompt = f.read()

user_prompt = ""
with open("prompts/claude3/haiku-v1/user.md", "r") as f:
    user_prompt = f.read()

reword_prompt = ""
with open("prompts/claude3/haiku-v1/reword.md", "r") as f:
    reword_prompt = f.read()


def get_prompts():
    """returns the haiku v1 prompts: system, user, reword"""
    return system_prompt, user_prompt, reword_prompt


def generate_message(messages,
                     model_id=model_id,
                     max_tokens=4096,
                     temperature=0.0,
                     top_p=0.999,
                     system_prompt="",
                     ):
    """generates a message using Claude 3 Haiku LLM"""

    logging.info("bedrock.converse()")

    request = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
        },
    }
    if system_prompt != "":
        request["system"] = [{'text': system_prompt}]

        response = bedrock.converse(
            modelId=model_id,
            messages=messages,
            system=[{'text': system_prompt}],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p,
            },
        )
    else:
        response = bedrock.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p,
            },
        )

    log.llm(request, response)

    stop_reason = response["stopReason"]
    if stop_reason != "end_turn":
        raise Exception(f"invalid stopReason returned from model: {stop_reason}")

    return response["output"]["message"]["content"][0]["text"]
