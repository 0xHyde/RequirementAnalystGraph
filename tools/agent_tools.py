import base64
from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_community.document_transformers.long_context_reorder import LongContextReorder
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

_ = load_dotenv(find_dotenv())
search = GoogleSearchAPIWrapper()

openai_api_key='ak-FYgTLggiUxnOpWhXokDGY4J7gNX7ueDhjAdeXVmTTpaBH6ln'
openai_api_base='https://api.nextapi.fun/v1'

# 谷歌搜索
@tool
def google_search(query: str) -> list:
    """Search with Google search"""
    return search.results(query,5)


# 网页内容查询
@tool
def web_scraping_search(link: Annotated[str, "The web address you need to visit"],
                        query: Annotated[str, "The topic of the information you want to obtain"]) -> list:
    """Visit the web page and retrieve the content. This tool is very useful for obtaining the content of the web page."""
    urls = [link]
    docs=[]

    # Load HTML
    loader = AsyncChromiumLoader(urls)
    html = loader.load()

    # Transform
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(
        html, tags_to_extract=["p", "li", "div", "a"]
    )

    # text splitter
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=50
    )
    splits = splitter.split_documents(docs_transformed)

    # load vectorstore
    embeddings = OpenAIEmbeddings(model='text-embedding-3-large',
                                  openai_api_key=openai_api_key,
                                  openai_api_base=openai_api_base)
    vectorstore = FAISS.from_documents(splits, embeddings)
    mmr_retriever = vectorstore.as_retriever(search_type="mmr", k=6, search_kwargs={"score_threshold": 0.5})
    docs = mmr_retriever.get_relevant_documents(query)

    # 文档压缩
    llm = ChatOpenAI(temperature=0)
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=mmr_retriever
    )
    compressed_docs = compression_retriever.get_relevant_documents(query)

    # 文档重新排序
    reordering = LongContextReorder()
    reordered_docs = reordering.transform_documents(compressed_docs)

    return reordered_docs

# 维基百科
@tool
def wikipedia_search(query: str) -> list:
    """Search for content from Wikipedia"""
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    result =  wikipedia.run(query)
    if result is None:
        return f'Unable to find the information of {query} from Wikipedia'
    else:
        return result

# Python 调用

repl = PythonREPL()

@tool
def python_repl(
    code: Annotated[str, "The python code to execute to generate your chart."]
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Succesfully executed:\n```python\n{code}\n```\nStdout: {result}"

# mermaid 图形绘制
@tool
def mermaid_graph(mermaid_code:str) -> str:
    """
    Drawing charts according to mermaid syntax is very useful for icon drawing.
    Input and output constraints: This tool only accepts mermaid syntax input and prohibits entering other irrelevant content. Please do not use /n and other ways to change the input content. Please use a multi-line string to represent it.. The tool will return the url address of the picture.
    The chart types supported by the tool are:Flowchart/Sequence Diagram/Class Diagram/State Diagram/Entity Relationship Diagram/User Journey/Gantt/Pie Chart/Quadrant Chart/Requirement Diagram/Gitgraph (Git) Diagram/C4 Diagram/Mindmaps/Timeline/Zenuml/Sankey/XYChart/Block Diagram/
    """
    graphbytes = mermaid_code.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    url="https://mermaid.ink/img/" + base64_string
    return url

