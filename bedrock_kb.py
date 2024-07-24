import os
import logging
import boto3
import log
import urllib

knowledge_base_id = os.environ.get("KNOWLEDGE_BASE_ID")
logging.warning(f"using knowledge base id {knowledge_base_id}")
kb = boto3.client('bedrock-agent-runtime')


def get_relevant_docs(query, top_k):
    """retrieves relevant documents from a vector store"""

    response = kb.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": top_k,
            }
        },
        retrievalQuery={"text": query}
    )
    logging.info(
        f"kb response found {len(response['retrievalResults'])} results")
    log.debug(response)

    return response["retrievalResults"]


def format_sources(sources):
    """
    Formats source docs in a standard format.

    Return dict example:
    [
        {
            "name": "MyDocument.pdf",
            "url": "https://document-server/MyDocument.pdf"
            "score": .8525
        }
    ]
    """

    result = []
    for source in sources:
        key = ""
        if source["location"]["type"] == "S3":

            # remove s3 bucket prefix for name and dedupe
            parsed = urllib.parse.urlparse(
                source["location"]["s3Location"]["uri"])
            key = parsed.path.lstrip("/")

            # todo: get presigned url
            url = ""

        # dedupe
        if not any(d["name"] == key for d in result):
            result.append({
                "name": key,
                "url": url,
                "score": source["score"],
            })

    return result
