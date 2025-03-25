# Command Line Interface Demo of Proscenium

## Help

```bash
python -m demo.cli --help
```

```text
Proscenium 🎭
The AI Alliance

                                                                                
 Usage: python -m demo.cli [OPTIONS] COMMAND [ARGS]...                          
                                                                                
 CLI Demo of Proscenium                                                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.      │
│ --show-completion             Show completion for the current shell, to copy │
│                               it or customize the installation.              │
│ --help                        Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ literature   Question answering using RAG on a text from the Gutenberg       │
│              Project.                                                        │
│ legal        Graph extraction and question answering with GraphRAG on        │
│              caselaw.                                                        │
│ abacus       Arithmetic question answering.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Abacus (Tool Use)

```bash
python -m demo.cli abacus --help
```

```text
Proscenium 🎭
The AI Alliance

                                                                                
 Usage: python -m demo.cli abacus [OPTIONS] COMMAND [ARGS]...                   
                                                                                
 Arithmetic question answering.                                                 
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ ask         Ask a natural langauge arithmetic question.                      │
│ ask-actor                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Literature (RAG)

```bash
python -m demo.cli literature --help
```

```text
Proscenium 🎭
The AI Alliance

                                                                                
 Usage: python -m demo.cli literature [OPTIONS] COMMAND [ARGS]...               
                                                                                
 Question answering using RAG on a text from the Gutenberg Project.             
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ prepare   Build a vector database from chunks of                             │
│           https://www.gutenberg.org/cache/epub/8714/pg8714.txt.              │
│ ask       Ask a question about literature using the RAG pattern with the     │
│           chunks prepared in the previous step.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Legal (GraphRAG)

```bash
python -m demo.cli legal --help
```

```text
Proscenium 🎭
The AI Alliance

                                                                                
 Usage: python -m demo.cli legal [OPTIONS] COMMAND [ARGS]...                    
                                                                                
 Graph extraction and question answering with GraphRAG on caselaw.              
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ extract                                                                      │
│ load-graph                                                                   │
│ show-graph                                                                   │
│ load-resolver                                                                │
│ ask                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### History

Taken from python notebook on a [branch](https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb)
