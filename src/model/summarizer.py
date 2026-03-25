import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import tensorflow as tf
from transformers import pipeline, TFAutoModelForSeq2SeqLM, AutoTokenizer

class VideoSummarizer:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6"):
        
        print(f"Initializing Summarizer Pipeline using {model_name}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            self.model = TFAutoModelForSeq2SeqLM.from_pretrained(model_name, from_pt=True)
            
            self.summarizer = pipeline(
                "summarization", 
                model=self.model, 
                tokenizer=self.tokenizer,
                framework="tf"
            )
            print("Summarizer Pipeline Ready.")
            
        except Exception as e:
            print(f"Failed to load summarization model: {e}")
            self.summarizer = None

    def generate_summary(self, text, max_length=130, min_length=30):
        
        if self.summarizer is None:
            return "Summarization model unavailable."

        if not text or len(text.strip()) < 50:
            return "Transcript too short or unavailable to generate a meaningful summary."

        max_input_chars = 4000 
        truncated_text = text[:max_input_chars]

        try:
            print("Generating summary...")
            summary_output = self.summarizer(
                truncated_text, 
                max_length=max_length, 
                min_length=min_length, 
                do_sample=False 
            )
            
            summary_text = summary_output[0]['summary_text']
            return summary_text.strip()
            
        except Exception as e:
            print(f"Summarization failed: {e}")
            return "Error generating summary due to model constraints."

if __name__ == "__main__":
    summarizer = VideoSummarizer()
    
    sample_transcript = """
    Welcome back to the channel! Today we are looking at the new features in Python 3.12. 
    A lot of developers have been waiting for these updates. The most significant change 
    is the improvement in error messages. In previous versions, missing a quote or a parenthesis 
    would give you a confusing SyntaxError pointing to the wrong line. Now, Python 3.12 
    specifically tells you exactly what is missing and where. Furthermore, they have introduced 
    performance enhancements under the hood, meaning your loops and function calls will run 
    marginally faster without changing any code. Finally, there are new typing features that 
    make static analysis tools much more accurate. Overall, this is a fantastic release 
    for both beginners and advanced developers. Make sure to like and subscribe!
    """
    
    print("\nGenerating Test Summary...")
    summary = summarizer.generate_summary(sample_transcript)
    print(f"\nFinal Summary:\n{summary}")