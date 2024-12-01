Privacy Warning: This code enables a webcam and takes pictures. These pictures are stored locally but are sent to openAI for image understanding.

The is code for part of a halloween installation.  Run

python simpleDialogue.py

to have conversation generated for two skeletons who are former miners.  Every so often a picture is taken and the skeletons
comment on costumes that people are wearing in the crowd.  preamble.txt gives the backstory in more detail.

This code depends upon openCV, OpenAI and ElevenLabs APIs.  To get those libraries:
  pip install opencv-python
  pip install openai
  pip install elevenlabs
