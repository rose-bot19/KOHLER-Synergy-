import os

import chromadb


CHROMA_PATH = "data/chroma_db"
KNOWLEDGE_ROOT = "knowledge"


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
}


def get_collection():
    """Create or load the Synergy knowledge collection."""

    os.makedirs("data", exist_ok=True)

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    return client.get_or_create_collection(
        name="kohler_knowledge"
    )


def chunk_text(text):
    """Split a document into useful sections."""

    chunks = []

    sections = text.split("\n\n")

    for section in sections:

        section = section.strip()

        if section:
            chunks.append(section)

    return chunks


def get_knowledge_files():
    """Find all supported documents in the knowledge folder."""

    files = []

    if not os.path.exists(KNOWLEDGE_ROOT):
        return files

    for root, directories, filenames in os.walk(
        KNOWLEDGE_ROOT
    ):

        for filename in filenames:

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension in SUPPORTED_EXTENSIONS:

                files.append(
                    os.path.join(
                        root,
                        filename
                    )
                )

    return files


def index_document(
    file_path,
    extra_metadata=None,
):
    """
    Add one document to Chroma.

    Existing chunks from the same source are removed first.
    """

    collection = get_collection()

    metadata = {
        "source": file_path,
        "status": "active",
    }

    if extra_metadata:
        metadata.update(
            extra_metadata
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()


    #READ TEXT / MARKDOWN

    if extension in {".txt", ".md"}:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            text = file.read()


    #READ PDF

    elif extension == ".pdf":

        from pypdf import PdfReader

        reader = PdfReader(
            file_path
        )

        pages = []

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        text = "\n\n".join(
            pages
        )


    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )


    chunks = chunk_text(text)


    collection.delete(
        where={
            "source": file_path
        }
    )


    ids = []
    documents = []
    metadatas = []


    for index, chunk in enumerate(chunks):

        ids.append(
            f"{file_path}_{index}"
        )

        documents.append(
            chunk
        )

        chunk_metadata = metadata.copy()

        chunk_metadata["chunk"] = index

        metadatas.append(
            chunk_metadata
        )


    if chunks:

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )


def build_knowledge_base():
    """Index all documents currently stored in knowledge."""

    files = get_knowledge_files()

    for file_path in files:

        index_document(
            file_path
        )

    return get_collection()


def search_knowledge(
    query,
    number_of_results=3,
):
    """Perform semantic search over active knowledge."""

    collection = get_collection()


    if collection.count() == 0:

        build_knowledge_base()


    return collection.query(

        query_texts=[
            query
        ],

        n_results=min(
            number_of_results,
            collection.count(),
        ),

        where={
            "status": "active"
        },
    )
