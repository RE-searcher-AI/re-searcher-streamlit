import json

from client import openai_client
from consts import openai_chat_model, use_pinecone, chat_max_tokens, generate_suggested_messages
from services.chat.chat_system_prompts import get_citations_system_message, get_system_prompt, format_system_message
from services.documents.douments_service import get_citations_from_pinecone, get_improved_query_message
from services.sticky_notes.sticky_notes_service import get_openai_functions, create_sticky_note
from services.suggestions.suggestion_service import generate_continuation_questions


def generate_chat_response(user_message_body):
    # 1. Extract user message
    document = user_message_body["active_document"]
    conversation = user_message_body["conversation"]

    response_message = ""
    sticky_note = None

    # 2. Find relevant info from documents -> insert doc data into context
    message_query = get_improved_query_message(user_message_body["conversation"])
    citations = get_citations(message_query, document["filename"])
    conversation.append(format_system_message(get_citations_system_message(citations)))
    conversation.insert(0, format_system_message(get_system_prompt(document)))

    # 3. Call OpenAI API:
    #   -> Generate response with citation
    #   -> Address function: -> Add sticky note
    #                        -> List keywords for that document
    response = openai_client.chat.completions.create(
        model=openai_chat_model,
        messages=conversation,
        tools=get_openai_functions(),
        tool_choice="auto",
        max_tokens=chat_max_tokens
    )

    # 3.5 Check for function calls
    first_choice = response.choices[0].message
    function_call = first_choice.tool_calls

    if function_call:
        function_name = function_call[0].function.name
        function_params = json.loads(function_call[0].function.arguments)

        print(f"Function called: {function_name}")
        if function_name == "create_sticky_note":
            sticky_note = create_sticky_note(function_params["title"], function_params["description"])
            response_message = "Beleška uspešno dodata!"
            conversation.append({"role": "assistant", "content": response_message})
            citations = []

    else:
        response_message = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": response_message})

    # 4. Shorten the conversation
    conversation = shorten_conversation(conversation)

    # 5. Generate a suggested message based on the chat context
    if generate_suggested_messages:
        continuation_questions = generate_continuation_questions(conversation)
    else:
        continuation_questions = None

    # 6. Format response
    return format_response(conversation=conversation, assistant_response=response_message, new_sticky_note=sticky_note,
                           citations=citations, continuation_questions=continuation_questions)


"""
name: format_response
params: 
    conversation -> user data body JSON subarray containing conversation roles
    assistant_response -> OpanAI API call return value based on the  
    new_sticky_note -> returns object of type StickyNote in case user explicitly demands a sticky note to be created
    citations -> user data body JSON subarray containing document citation done by bedrock
description: response returns a key map containing conversational elements
"""


def format_response(conversation, assistant_response, new_sticky_note, citations,
                    continuation_questions):
    return {
        "conversation": conversation,
        "assistant_response": assistant_response,
        "new_sticky_note": new_sticky_note,
        "citations": citations,
        "continuation_questions": continuation_questions
    }


"""
name: shorten_conversation
params: messages list
description: shortens the messages list by retaining the last 20 elements.
In case list is shorter than 20 elements, it will display the whole list.
"""


def shorten_conversation(messages):
    messages = messages[-20:]
    return [message for message in messages if message.get("role") != "system"]


def get_citations(user_message, filename, topic=None):
    if use_pinecone:
        return get_citations_from_pinecone(user_message, filename, topic)

    else:
        return []
