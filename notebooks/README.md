# Proscenium Demo Notebooks

These notebooks default to using a `TOGETHER_API_KEY`, available from [Together.AI](https://together.ai/).
To use another inference platform, replace the `model_id` string with any valid
model identifier for [AI Suite](https://github.com/andrewyng/aisuite/).

## Legal

[Legal.ipynb](./Legal.ipynb) demonstrates using an LLM to extract and resolve a Knowledge Graph from
publicly available legal opinions.

It requires a Neo4j instance in addition to an inference service.

<a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Legal.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

## Literature

[Literature.ipynb](./Literature.ipynb) demonstrates using a vector database to store chunks of two books,
and using those chunks to form a context for LLM inference based on a user question (the Retrieval Augmented Generation pattern, aka "RAG".)

<a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Literature.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

## Abacus

[Abacus.ipynb](./Abacus.ipynb)

<a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Abacus-Tools.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
