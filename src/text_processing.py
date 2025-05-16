import spacy
from spacy.util import is_package
import spacy.cli
from typing import List

MODEL_NAME = 'en_core_web_sm'

def ensure_model_installed():
    """Ensure the SpaCy model is installed, downloading it if necessary."""
    if not is_package(MODEL_NAME):
        print(f"{MODEL_NAME} not found. Attempting to download...")
        try:
            spacy.cli.download(MODEL_NAME)
            print(f"Successfully downloaded {MODEL_NAME}.")
        except Exception as e:
            print(f"Error downloading {MODEL_NAME}: {e}")
            print("Please try downloading the model manually with 'python -m spacy download en_core_web_sm'.")
    else:
        print(f"{MODEL_NAME} is already installed.")

ensure_model_installed()

# Load the model after ensuring it's installed
nlp = spacy.load(MODEL_NAME)


def split_into_chunks(text: str, min_words: int = 200, max_words: int = 500) -> List[str]:
    """
    Splits the text into chunks based on paragraph boundaries and sentence boundaries for long paragraphs.
    
    :param text: The raw text to be processed.
    :param min_words: Minimum number of words in a chunk.
    :param max_words: Maximum number of words in a chunk.
    :return: A list of text chunks.
    """
    paragraphs = text.split('\n\n')  # Split text into paragraphs
    chunks = []
    current_chunk = []
    current_word_count = 0

    for paragraph in paragraphs:
        doc = nlp(paragraph)
        paragraph_word_count = len(doc)

        if paragraph_word_count > 500:
            # Split long paragraphs into smaller chunks using sentence boundaries
            sentence_chunk = []
            sentence_word_count = 0

            for sentence in doc.sents:
                sentence_word_count += len(sentence)
                sentence_chunk.append(sentence.text)

                if sentence_word_count >= max_words:
                    chunks.append(' '.join(sentence_chunk))
                    sentence_chunk = []
                    sentence_word_count = 0

            if sentence_chunk:
                chunks.append(' '.join(sentence_chunk))
        else:
            # Add paragraph to the current chunk
            current_chunk.append(paragraph)
            current_word_count += paragraph_word_count

            if min_words <= current_word_count <= max_words:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_word_count = 0

    # Add any remaining text as a final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def add_chunk_markers(text: str) -> str:
    """
    Adds HTML chunk markers to the text based on paragraph boundaries.
    
    :param text: The raw text to be processed.
    :return: The text with chunk markers added.
    """
    chunks = split_into_chunks(text)
    marked_text = ''

    for i, chunk in enumerate(chunks, start=1):
        marked_text += f'<chunk{i}>{chunk}</chunk{i}>\n\n'

    return marked_text.strip()