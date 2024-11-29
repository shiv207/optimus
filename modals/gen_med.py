import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_medical_ai():
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv('NVIDIA_API_KEY')
    )

def med_prompt_stream(prompt: str):
    """
    Stream responses from the medical AI model
    """
    try:
        client = initialize_medical_ai()
        
        completion = client.chat.completions.create(
            model="writer/palmyra-med-70b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=True
        )

        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"Medical AI Error: {str(e)}"

def is_medical_query(prompt: str) -> bool:
    """
    Determine if a query is medical-related
    """
    medical_keywords = [
        'disease', 'treatment', 'symptoms', 'diagnosis', 'medicine', 'medical',
        'health', 'doctor', 'hospital', 'patient', 'cure', 'therapy', 'drug',
        'prescription', 'condition', 'illness', 'syndrome', 'disorder', 'pain',
        'infection', 'vaccine', 'surgery', 'medication', 'clinical', 'physician',
        'healthcare', 'nursing', 'emergency', 'chronic', 'acute', 'pathology',
        'anatomy', 'physiology', 'cancer', 'diabetes', 'heart', 'brain', 'lung',
        'liver', 'kidney', 'blood', 'immune', 'virus', 'bacterial'
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in medical_keywords)