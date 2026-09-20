import os

import chromadb


MEMORY_PATH = "data/memory_db"


def get_memory_collection():

    os.makedirs(
        "data",
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=MEMORY_PATH
    )

    return client.get_or_create_collection(
        name="synergy_memory"
    )


def remember_episode(
    summary,
    tags=None
):

    if tags is None:
        tags = []

    collection = (
        get_memory_collection()
    )

    memory_id = (
        f"memory_{collection.count() + 1}"
    )

    collection.upsert(

        ids=[
            memory_id
        ],

        documents=[
            summary
        ],

        metadatas=[{

            "tags":
                ", ".join(tags),

            "type":
                "episodic",

        }],
    )

    return {
        "id":
            memory_id,

        "summary":
            summary,

        "tags":
            tags,
    }


def search_memory(
    query,
    limit=3
):

    collection = (
        get_memory_collection()
    )

    count = collection.count()

    if count == 0:
        return []


    results = collection.query(

        query_texts=[
            query
        ],

        n_results=min(
            limit,
            count
        ),
    )


    memories = []

    documents = (
        results.get(
            "documents",
            [[]]
        )[0]
    )

    metadatas = (
        results.get(
            "metadatas",
            [[]]
        )[0]
    )


    for document, metadata in zip(
        documents,
        metadatas
    ):

        memories.append({

            "summary":
                document,

            "metadata":
                metadata,

        })


    return memories