from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import os
import shutil
import sys
import argparse
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


IMG_READ_PROMPT = """##### 角色
你是一位出色的图片解读者，擅长从图片中解读细节并能为其创作详尽的描述、生成标签和名字
##### 任务
###### 任务1: 图片解读和描述
- 分析图片，挖掘图片背后的故事以及图片展现出来的氛围，意境和情感。
- 基于图片内容，创作出详尽、引人入胜的文字描述。
###### 任务2: 生成图片标签
- 基于图片内容和描述，图片背后的故事以及图片展现出来的氛围，意境和情感，生成图片标签。
- 标签内容类别包括且不限于图片内容，如景物、节日、季节、动物、植物、高山、流水、街道、房屋、城市。图片寓意如氛围、情感、情绪等。
###### 任务3: 生成图片名字
- 基于图片内容和描述，生成简短的名字
- 名字能快速让读者知道图片内容
##### 要求
- 描述与图片应紧密相连，需包含图片的寓意，如氛围、情感、情绪，且尽可能详实，且不偏离图片本身的内容。
- 标签使用名词，且不多于5个，以英文逗号分割，如"街道,建筑,日本,昭和时代,怀旧"。
- 图片标签要简洁、以形容词加名词组合，如"昭和时代的街道","车水马龙的城市", "伤心哭泣的女人"。
##### 输出格式
以JSON提供您的输出，JSON的key为desc("图片描述")，label("图片标签")，name（"图片名字")"""

llm = ChatGoogleGenerativeAI(model="gemini-pro-vision", temperature = 0, google_api_key = st.secrets["APP_KEY"])

def read_image(image_path):
    try:
        message = HumanMessage(
            content=[
                {"type": "text", "text": IMG_READ_PROMPT},
                {"type": "image_url", "image_url": image_path}
            ]
        )
        result = llm.invoke([message])
        response_schemas = [
            ResponseSchema(name="desc", description="图片描述"),
            ResponseSchema(name="label", description="图片标签"),
            ResponseSchema(name="name", description="图片名字")
        ]
        parser = StructuredOutputParser.from_response_schemas(response_schemas)
        json_dic = parser.parse(result.content)
        label = json_dic['label']
        desc = json_dic['desc']
        name = json_dic['name']
        
        image_new_name = name + os.path.splitext(image_path)[1]
        final_path = os.path.join(os.path.dirname(image_path), image_new_name)
        shutil.move(image_path, final_path)

        print(f"mv {image_path} to {final_path}")
        print(f"name:{name}")
        print(f"label:{label}")
        print(f"desc:{desc}")
        print(f"-----------------------------------------------------------------------")

    except Exception as e:
        print(f"ai can not read {image_path}, {e}")


def monitor_directory(directory):
    """
    Monitor a directory for new files.

    Args:
        directory: The directory to monitor.

    Returns:
        A list of new files in the directory.
    """

    # Get the current list of files in the directory.
    current_files = os.listdir(directory)

    # Loop forever, checking for new files.
    while True:
        # Sleep for a second.
        time.sleep(1)

        # Get the new list of files in the directory.
        new_files = os.listdir(directory)

        # Find the new files that were not in the previous list.
        diff_new_files = set(new_files) - set(current_files)

        # to read image file
        if len(diff_new_files) > 0 and len(new_files) != len(current_files):
            print(f"new files: {diff_new_files}")
            for file in diff_new_files:
                read_image(os.path.join(directory, file))

        # Update the current list of files.
        current_files = new_files

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Directory to monitor')
    parser.add_argument('--monitor', default=False, help='to monitor or not')
    args = parser.parse_args()
    path = args.path
    to_monitor = args.monitor
    print(path, to_monitor)
    if to_monitor:
        monitor_directory(path)
    else:
        if os.path.isfile(path):
            read_image(path)
        else:
            for file in os.listdir(path):
                read_image(os.path.join(path, file))
    

if __name__ == "__main__":
    main()
    

        





