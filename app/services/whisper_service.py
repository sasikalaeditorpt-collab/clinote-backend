import whisper

model = whisper.load_model("medium")

def transcribe_audio(path: str) -> str:
    result = model.transcribe(path)
    return result["text"]