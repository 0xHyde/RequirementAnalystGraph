import os

import time
import jwt
from langchain_openai import ChatOpenAI
from dotenv import find_dotenv, load_dotenv


_ = load_dotenv(find_dotenv())

def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )

def chat_glm4(temperature:float = 0.2, streaming:bool = True):
    zhipu_api_token = generate_token(apikey=os.getenv("ZHIPUAI_API_KEY"), exp_seconds=7200)
    llm_temperature = temperature
    if llm_temperature ==0:
        llm_temperature = 0.001
    llm = ChatOpenAI(model_name="glm-4",
                     api_key=zhipu_api_token,
                     openai_api_base="https://open.bigmodel.cn/api/paas/v4",
                     temperature=llm_temperature,
                     streaming=streaming
                     )
    return llm