from client import openai_client
from consts import min_score, openai_completions_model, pinecone_query_max_tokes
from services.documents.embeddings_service import separate_text_from_pdf, chunk_text, get_embeddings_for_chunks, \
    get_embeddings
from services.documents.pinecone_service import upsert_pinecone_vectors, query_pinecone_vectors
from services.suggestions.suggestion_service import extract_recent_messages


def upload_document_to_pinecone(file, topic, name, description):
    filename = file.filename
    topics = [topic]

    document_text = separate_text_from_pdf(file)
    chunks = chunk_text(document_text)
    embeddings = get_embeddings_for_chunks(chunks)
    upsert_pinecone_vectors(embeddings, chunks, filename, topics)
    return f"Success! [{name}]"


def get_citations_from_pinecone(user_message, filename, topic=None):
    user_message_embedding = get_embeddings(user_message)

    pinecone_results = query_pinecone_vectors(user_message_embedding, filename, topic)
    matches = pinecone_results['matches']

    sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    filtered_matches = [x for x in sorted_matches if x['score'] > min_score]
    content_list = [{"content": match['metadata']['content'],
                     "filename": match['metadata']['filename'],
                     "score": match['score']
                     } for match in filtered_matches]

    return content_list


def get_improved_query_message_prompt(recent_messages_json_string):
    return f"""
Vi ste asistent koji generiše sažete i kontekstualno bogate upitne stringove za vektorsku bazu podataka u 
Retrieval-Augmented Generation (RAG) sistemu. Cilj je poboljšati relevantnost rezultata pretrage sažimanjem 
poslednjih nekoliko poruka između korisnika i AI u jedan efikasan upit.

Obezbedite da upit bude jasan i fokusiran na glavnu temu diskusije, dok minimizirate zavisnost od specifičnih 
korisničkih izraza.

Fokus upita treba da bude poslednja korisnikova poruka, i pitanje koje ona nosi.

U nastavku je istorija konverzacije korisnika i vestacke inteligencije na osnovu koje treba da generises upit: 

${recent_messages_json_string}

Za gore datu konverzaciju, generisi upit: 
"""


def get_improved_query_message(conversation_context):
    conversation = extract_recent_messages(conversation_context)

    try:
        response = openai_client.completions.create(
            model=openai_completions_model,
            prompt=get_improved_query_message_prompt(conversation),
            max_tokens=pinecone_query_max_tokes,
        )

        return response.choices[0].text
    except:
        return conversation_context[-1]["content"]
