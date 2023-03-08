import os
import openai
import json
from enum import Enum
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

PROMPT = """
you are a domotic robot You manage three systems [thermostat, shutter, music]. You have to detect the system that need to be updated.
- thermostat is a system that manage the house temperature, the scale of accepted values are all number values between the freshed 14 and the hottest 25. Try to infer the best value following user need.
- music is used to play song in house, accepted values are all the song names that could be used in a third party system like spotify or deezer or just stop if the user request to stop
- rolling_shutter is used to open or close the rolling shutter

Provide as an answer an object containing the system to update and the value used. The keys of the object should be [type, system, value, explaination, user_message]
If a system is well detected the type is "success".
If the user request didn't fit any of the requested system and values, provide the following answer {{"type": "error", "message": "no valid system detected"}}

The explaination key contains the reason why you choose this solution
The user_message key contains a small answer for the user

format all answer as a json string
"""

templates = Jinja2Templates(directory="templates")
app = FastAPI()


class SystemEnum(Enum):
    THERMOSTAT = "thermostat"
    ROLLING_SHUTTER = "rolling_shutter"
    MUSIC = "music"


class HouseCommand(BaseModel):
    system: SystemEnum  
    value: str | int


class UserRequestInput(BaseModel):
    request: str

command_logs = []


class HouseSystem:
    temperature = 20
    shutter = "open"
    music = None

    def update_temperature(self, temperature: int):
        if 14 <= self.temperature <= 25:
            self.temperature = temperature
        else:
            raise Exception("Invalid temperature %s" % temperature)

    def update_shutter(self, requested_state: str):
        if requested_state == "open" or requested_state == "close":
            self.shutter = requested_state
        else:
            raise Exception("Invalid shutter state requested %s" % requested_state)

    def update_music(self, song: str | None):
        self.music = song


def assistant(content):
    return {"role": "assistant", "content": content}

def user(content):
    return {"role": "user", "content": content}

def system(content):
    return {"role": "system", "content": content}

def chat(message: str, stack: list):
    
    stack.append(user(message))

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=stack,
        temperature=0
    )

    data = response["choices"][0]

    return data["message"]["role"], data["message"]["content"]

house = HouseSystem()

def deal_with_the_command(command: HouseCommand):
    if command.system == SystemEnum.MUSIC:
        house.update_music(command.value)
    elif command.system == SystemEnum.ROLLING_SHUTTER:
        house.update_shutter(int(command.value))
    elif command.system == SystemEnum.THERMOSTAT:
        house.update_temperature(command.value)
    else:
        raise Exception("Unknown system")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("app/home.html", {"request": request})


@app.post("/input")
async def natural_language_input(user_request_input: UserRequestInput):
    stack = [
        system(PROMPT),
        assistant(f"Current situation thermostat: {house.temperature}, shutter: {house.shutter}, music: {house.music}")
    ]
    (_, answer) = chat(user_request_input.request, stack)
    print("answer", answer, stack)
    try:
        parsed_response = json.loads(answer)
        command_logs.append(parsed_response)

        if parsed_response["type"] == "success":
            deal_with_the_command(HouseCommand(**{
                "system": parsed_response["system"],
                "value": parsed_response["value"]
            }))
            print(house.temperature)
            return {"status": "ok"}
        else:
            return parsed_response
    except Exception as e:
        return {"status": "failure", "message": str(e)}
    

@app.get("/logs")
async def logs(skip: int = 0, limit: int = 10):
    return command_logs[skip: skip + limit]


@app.get("/state")
async def state():
    return {
        "thermostat": house.temperature,
        "music": house.music,
        "shutter": house.shutter
    }


app.mount("/static", StaticFiles(directory="static"), name="static")