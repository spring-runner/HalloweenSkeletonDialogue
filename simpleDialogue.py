""" A simple dialogue between two skeletons using the ElevenLabs and OpenAI APIs. """

import logging
import os
import random
import time
from typing import Tuple
from typing import List

from elevenlabs import play, VoiceSettings
from elevenlabs.client import ElevenLabs
from openai import OpenAI

from camera import Camera

# ElevenLabs voice IDs for the two skeletons.
DAVE_VOICE_ID = "qNkzaJoHLLdpvgh5tISm"
NELLIE_VOICE_ID = "ZVRPpjKhYf99eP21TZDZ"

# The preamble for the dialogue.
PREAMBLE_FILE = "preamble.txt"

# File to write logs to.
LOG_DIR = "Logs"
LOG_FILE = f'{time.strftime("%a-%b-%d-%Y.%H:%M:%S", time.localtime())}.log'

def setup_ai_clients()->Tuple[ElevenLabs, OpenAI]:
    """ Load the API keys from the environment variables where they are stored.

    Raises: ValueError: If the API keys are not set.
    Returns: A tuple of the ElevenLabs and OpenAI clients.
    See https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
    for more info on how to store API keys securely.
    """
    eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if eleven_labs_api_key is None:
        raise ValueError("ELEVENLABS_API_KEY is not set.")
    eleven_client = ElevenLabs(api_key=eleven_labs_api_key)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("openai_api_key is not set.")
    openai_client = OpenAI(api_key=openai_api_key)
    return (eleven_client, openai_client)

def text_to_speech(text: str, voice: str, eleven_client: ElevenLabs)->None:
    """Calling the text_to_speech conversion API with detailed parameters. """

    response = eleven_client.text_to_speech.convert(
        voice_id = voice,
        output_format = "mp3_22050_32",
        text = text,
        model_id = "eleven_turbo_v2_5", # use the turbo model for low latency
        voice_settings = VoiceSettings(
            stability = 0.0,
            similarity_boost = 1.0,
            style = 0.0,
            use_speaker_boost = True,
        ),
    )

    play(response)

def get_skeleton_response(skeleton_name: str,
                          image_url: str,
                          conversation_history: List[str],
                          openai_client: OpenAI)->str:
    """ Get the next line of dialogue from the skeleton. 
    
    If image_url is not none, then the skeletons will comment on the image.
    Otherwise, they will just extend the dialogue.
    """

    # Decide whether to ask for a comment on an image or the next line of dialogue.
    if image_url is None:
        conversation_history.append(
            { "role" : "user", "content" : f"What does {skeleton_name} say?"} )
    else:
        conversation_history.append( {
            "role" : "user",
            "content" : [
                { "type" : "text", "text" : f"What does {skeleton_name} say about this image?" },
                { "type" : "image_url", "image_url" : { "url" : image_url } }
            ]
        })

    response = openai_client.chat.completions.create(
        model = "gpt-4-turbo",
        messages = conversation_history
    )

    # Extract what the skeleton said from the gpt-4-turbo response.
    skeleton_response = response.choices[0].message.content
    if skeleton_response[0] == '"' and skeleton_response[-1] == '"':
        skeleton_response = skeleton_response[1:-1]

    conversation_history.append( { "role" : "assistant", "content" : skeleton_response } )
    return skeleton_response

def run_dialogue(elevenlabs_client: ElevenLabs,
                 openai_client: OpenAI,
                 camera: Camera,
                 preamble: str)->None:
    """ Run the dialogue between the two skeletons. """
    conversation_history = [{ "role" : "system", "content" : preamble }]
    skeleton_num = 0
    skeleton_names = [ "Nellie", "Dave" ]
    skeleton_voices = [ NELLIE_VOICE_ID, DAVE_VOICE_ID ]
    last_image_round = 0

    for r in range(10000):
        comments_since_image = r - last_image_round
        if comments_since_image >= 2 and random.random() < 0.5:
            image_url = camera.get_webcam_image_as_base64()
            logging.info(f"Image taken at {time.asctime()}\n")
            last_image_round = r
        else:
            image_url = None

        skeleton_num = r % 2
        skeleton_name = skeleton_names[skeleton_num]
        skeleton_voice = skeleton_voices[skeleton_num]
        skeleton_says = get_skeleton_response(skeleton_name, image_url,
                                              conversation_history, openai_client)

        log_entry = f"{time.asctime()} {skeleton_name}: {skeleton_says}\n"
        print(log_entry)
        logging.info(log_entry)

        text_to_speech(skeleton_says, skeleton_voice, elevenlabs_client)

if __name__ == "__main__":
    # Set up logging.
    if not os.path.exists(LOG_DIR):
        logging.info(f"Creating log directory {LOG_DIR}")
        os.makedirs(LOG_DIR)
    else:
        logging.info(f"Log directory {LOG_DIR} exists.")

    log_file_path = os.path.join(LOG_DIR, LOG_FILE)
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG)

    # Set up the AI clients.
    elevenlabs_client, openai_client = setup_ai_clients()

    # Create the camera object.
    camera = Camera(log_file_path)

    # Load the preamble from file.
    preamble = open(PREAMBLE_FILE, "r").read()

    run_dialogue(elevenlabs_client, openai_client, camera, preamble)

    del camera
